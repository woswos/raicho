import contextlib
import io
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime.credentials import raicho_connector_files as connector_files


class ConnectorSecretFilesTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-connector-files-')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)

    def operate(self, operation):
        return connector_files.operate(
            operation, self.directory, os.getuid(), os.getgid()
        )

    def path(self, name):
        return self.directory / f'connector.{name}'

    def initialized(self):
        self.assertEqual(self.operate('init'), 'pending')
        self.operate('publish')
        self.operate('finish')
        return self.path('token').read_bytes()

    def test_initialization_is_private_and_idempotent(self):
        self.directory.chmod(0o755)
        self.assertEqual(self.operate('init'), 'pending')
        pending = self.path('pending')
        token = pending.read_bytes()
        self.assertRegex(token, rb'\A[0-9a-f]{64}\n\Z')
        self.assertEqual(stat.S_IMODE(pending.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.directory.stat().st_mode), 0o700)
        self.assertEqual(
            (pending.stat().st_uid, pending.stat().st_gid), (os.getuid(), os.getgid())
        )
        self.assertEqual(self.operate('init'), 'pending')
        self.assertEqual(pending.read_bytes(), token)
        self.operate('publish')
        self.operate('finish')
        self.assertEqual(self.operate('init'), 'current')
        self.assertEqual(self.operate('check'), 'current')
        self.assertEqual(self.path('token').read_bytes(), token)

    def test_rotation_preserves_committed_file_until_finish(self):
        original = self.initialized()
        self.assertEqual(self.operate('rotate'), 'pending')
        replacement = self.path('pending').read_bytes()
        self.assertNotEqual(original, replacement)
        self.assertEqual(self.operate('rotate'), 'pending')
        self.assertEqual(self.path('pending').read_bytes(), replacement)
        self.operate('publish')
        self.assertEqual(self.path('previous').read_bytes(), original)
        self.assertEqual(self.path('token').read_bytes(), replacement)
        self.assertEqual(self.operate('rotate'), 'current')
        with self.assertRaises(ValueError):
            self.operate('check')
        self.operate('finish')
        self.assertFalse(self.path('previous').exists())
        self.assertEqual(self.operate('check'), 'current')

    def test_reactivation_resumes_prepared_replacement(self):
        self.initialized()
        self.operate('rotate')
        self.assertEqual(self.operate('reactivate'), 'pending')
        replacement = self.path('pending').read_bytes()
        self.assertEqual(self.operate('reactivate'), 'pending')
        self.assertEqual(self.path('pending').read_bytes(), replacement)
        self.operate('publish')
        self.assertEqual(self.operate('reactivate'), 'current')
        self.operate('finish')

    def test_reactivation_retries_after_publication_without_another_token(self):
        self.assertEqual(self.operate('reactivate'), 'pending')
        replacement = self.path('pending').read_bytes()
        self.operate('publish')
        self.assertEqual(self.operate('reactivate'), 'current')
        self.assertEqual(self.path('token').read_bytes(), replacement)
        self.assertFalse(self.path('pending').exists())
        self.operate('finish')
        self.assertEqual(self.operate('reactivate'), 'current')

    def test_reactivation_handles_missing_local_secret_files(self):
        self.directory.chmod(0o755)
        self.assertEqual(self.operate('reactivate'), 'pending')
        replacement = self.path('pending').read_bytes()
        self.assertEqual(self.operate('reactivate'), 'pending')
        self.assertEqual(self.path('pending').read_bytes(), replacement)
        self.operate('publish')
        self.operate('finish')
        self.assertEqual(self.operate('check'), 'current')

    def test_interrupted_publish_can_resume_without_new_token(self):
        original = self.initialized()
        self.operate('rotate')
        replacement = self.path('pending').read_bytes()
        replace = os.replace

        def interrupted_replace(source, destination, **arguments):
            if source == 'connector.pending':
                raise OSError('interrupted')
            return replace(source, destination, **arguments)

        with patch.object(connector_files.os, 'replace', interrupted_replace):
            with self.assertRaises(OSError):
                self.operate('publish')
        self.assertFalse(self.path('token').exists())
        self.assertEqual(self.operate('rotate'), 'pending')
        self.assertEqual(self.path('token').read_bytes(), original)
        self.assertEqual(self.path('pending').read_bytes(), replacement)
        self.operate('publish')
        self.operate('finish')
        self.assertEqual(self.path('token').read_bytes(), replacement)

    def test_insecure_files_directories_and_owner_fail_closed(self):
        original = self.initialized()
        for mode in (0o640, 0o644, 0o400, 0o700):
            with self.subTest(mode=mode):
                self.path('token').chmod(mode)
                with self.assertRaises(ValueError):
                    self.operate('rotate')
        self.path('token').chmod(0o600)
        self.directory.chmod(0o755)
        with self.assertRaises(ValueError):
            self.operate('init')
        self.directory.chmod(0o700)
        with self.assertRaises(ValueError):
            connector_files.operate(
                'check', self.directory, os.getuid() + 1, os.getgid()
            )
        self.assertEqual(self.path('token').read_bytes(), original)
        self.assertFalse(self.path('pending').exists())

    def test_rejects_links_nonregular_files_and_malformed_tokens(self):
        self.initialized()
        original = self.path('token').read_bytes()
        self.path('token').unlink()
        self.path('token').symlink_to('/dev/null')
        with self.assertRaises((ValueError, OSError)):
            self.operate('check')
        self.path('token').unlink()
        self.path('token').mkdir(mode=0o600)
        with self.assertRaises((ValueError, OSError)):
            self.operate('check')
        self.path('token').rmdir()
        os.mkfifo(self.path('token'), 0o600)
        with self.assertRaises(ValueError):
            self.operate('check')
        self.path('token').unlink()
        for contents in (b'', b'A' * 64, b'a' * 63, b'a' * 65, original + b'\n'):
            with self.subTest(contents=contents):
                self.path('token').write_bytes(contents)
                self.path('token').chmod(0o600)
                with self.assertRaises(ValueError):
                    self.operate('check')

    def test_rejects_directory_symlinks_and_hard_linked_secrets(self):
        original = self.initialized()
        directory_link = self.directory / 'linked_directory'
        directory_link.symlink_to(self.directory, target_is_directory=True)
        with self.assertRaises(OSError):
            connector_files.operate('check', directory_link, os.getuid(), os.getgid())
        directory_link.unlink()
        os.link(self.path('token'), self.path('pending'))
        with self.assertRaises(ValueError):
            self.operate('rotate')
        self.assertEqual(self.path('token').read_bytes(), original)

    def test_missing_and_inconsistent_states_fail_without_mutation(self):
        for operation in ('rotate', 'publish', 'finish', 'check'):
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                self.operate(operation)
        self.initialized()
        self.path('previous').write_bytes(b'b' * 64)
        self.path('previous').chmod(0o600)
        with self.assertRaises(ValueError):
            self.operate('init')
        self.path('pending').write_bytes(b'c' * 64)
        self.path('pending').chmod(0o600)
        for operation in ('rotate', 'publish', 'finish', 'check'):
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                self.operate(operation)

    def test_failed_preparation_removes_staging_and_preserves_current(self):
        original = self.initialized()
        with patch.object(connector_files.os, 'replace', side_effect=OSError('failed')):
            with self.assertRaises(OSError):
                self.operate('rotate')
        self.assertEqual(list(self.directory.iterdir()), [self.path('token')])
        self.assertEqual(self.path('token').read_bytes(), original)

    def test_killed_preparation_leaves_a_recoverable_directory(self):
        original = self.initialized()
        staging = self.directory / '.connector.preparing'
        staging.write_bytes(b'partial')
        self.assertEqual(self.operate('rotate'), 'pending')
        self.assertFalse(staging.exists())
        self.assertEqual(self.path('token').read_bytes(), original)
        self.path('pending').unlink()
        staging.symlink_to(self.path('token'))
        with self.assertRaises(ValueError):
            self.operate('check')
        self.assertTrue(staging.is_symlink())

    def test_rejects_unexpected_files_and_cli_never_prints_secret(self):
        secret = self.initialized()
        (self.directory / 'unexpected').touch()
        with self.assertRaises(ValueError):
            self.operate('init')
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            self.assertEqual(connector_files.main(['check', str(self.directory)]), 1)
        self.assertIn('FAIL:', errors.getvalue())
        self.assertNotIn(secret.decode().strip(), output.getvalue() + errors.getvalue())
        with patch.object(connector_files, 'operate', return_value='current'):
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                self.assertEqual(
                    connector_files.main(['check', str(self.directory)]), 0
                )
        self.assertEqual(output.getvalue(), 'current\n')
