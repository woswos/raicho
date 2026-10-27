import json
import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch

from mailprobe.tests.profile.credentials import write_credentials


class CredentialTests(unittest.TestCase):
    def test_login_realm_excludes_the_nonstandard_port(self):
        with tempfile.TemporaryDirectory() as directory:
            profile = Path(directory)
            library = object()
            with (
                patch(
                    'mailprobe.tests.profile.credentials.encryption_library',
                    return_value=nullcontext(library),
                ) as initialization,
                patch(
                    'mailprobe.tests.profile.credentials.encrypt',
                    side_effect=['encrypted username', 'encrypted password'],
                ) as encryption,
            ):
                write_credentials(profile)
            initialization.assert_called_once_with(profile)
            self.assertEqual(
                encryption.call_args_list,
                [
                    unittest.mock.call(library, 'sender'),
                    unittest.mock.call(library, 'fixture'),
                ],
            )
            destination = profile / 'logins.json'
            stored = json.loads(destination.read_text())
            self.assertEqual(stored['version'], 3)
            self.assertEqual(stored['nextId'], 2)
            self.assertEqual(len(stored['logins']), 1)
            login = stored['logins'][0]
            self.assertEqual(login['hostname'], 'imap://mail-proxy')
            self.assertEqual(login['httpRealm'], 'imap://mail-proxy')
            self.assertIsNone(login['formSubmitURL'])
            self.assertEqual(login['encType'], 1)
            self.assertEqual(login['encryptedUsername'], 'encrypted username')
            self.assertEqual(login['encryptedPassword'], 'encrypted password')
            self.assertNotIn('fixture', destination.read_text())
            self.assertEqual(destination.stat().st_mode & 0o777, 0o600)


if __name__ == '__main__':
    unittest.main()
