import os
import stat
from unittest.mock import patch

from runtime.credentials import raicho_connector_files as connector_files
from runtime.credentials.tests.raicho_connector_files_fixture import (
    ConnectorTokenFilesTestCase,
)


class ConnectorTokenStateTests(ConnectorTokenFilesTestCase):
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

    def test_reactivation_handles_missing_local_token_files(self):
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
