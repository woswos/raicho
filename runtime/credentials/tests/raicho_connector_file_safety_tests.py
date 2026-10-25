import contextlib
import io
import os
from unittest.mock import patch

from runtime.credentials import raicho_connector_files as connector_files
from runtime.credentials.tests.raicho_connector_files_fixture import (
    ConnectorTokenFilesTestCase,
)


class ConnectorTokenSafetyTests(ConnectorTokenFilesTestCase):
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

    def test_rejects_directory_symlinks_and_hard_linked_tokens(self):
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

    def test_rejects_unexpected_files_and_cli_never_prints_token(self):
        token = self.initialized()
        (self.directory / 'unexpected').touch()
        with self.assertRaises(ValueError):
            self.operate('init')
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            self.assertEqual(connector_files.main(['check', str(self.directory)]), 1)
        self.assertIn('FAIL:', errors.getvalue())
        self.assertNotIn(token.decode().strip(), output.getvalue() + errors.getvalue())
        with patch.object(connector_files, 'operate', return_value='current'):
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                self.assertEqual(
                    connector_files.main(['check', str(self.directory)]), 0
                )
        self.assertEqual(output.getvalue(), 'current\n')
