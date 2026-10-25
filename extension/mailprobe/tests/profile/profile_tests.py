import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from profile_settings import preferences
from seed_profile import MARKER, seed_profile


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.profile = Path(self.temporary.name) / 'profile'

    def seed(self):
        def write_credentials(profile):
            (profile / 'logins.json').write_text('{"fixture": true}')

        with patch('seed_profile.write_credentials', write_credentials):
            return seed_profile(self.profile)

    def test_seed_uses_private_profile_and_two_selected_identities(self):
        self.assertTrue(self.seed())
        self.assertEqual(self.profile.stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.profile / 'user.js').stat().st_mode & 0o777, 0o600)
        self.assertEqual((self.profile / MARKER).stat().st_mode & 0o777, 0o600)
        configured = {}
        for line in (self.profile / 'user.js').read_text().splitlines():
            name, value = json.loads('[' + line[len('user_pref(') : -2] + ']')
            configured[name] = value
        self.assertEqual(configured, preferences())
        self.assertEqual(configured['mail.account.account1.identities'], 'id1,id2')
        self.assertEqual(configured['mail.identity.id2.useremail'], 'alias@raicho.test')
        for identity in ['id1', 'id2']:
            self.assertEqual(
                configured[f'mail.identity.{identity}.draft_folder'],
                'imap://sender@mail-proxy/Drafts',
            )
            self.assertEqual(
                configured[f'mail.identity.{identity}.fcc_folder'],
                'imap://sender@mail-proxy/Sent',
            )

    def test_restart_preserves_user_preferences_and_credentials(self):
        self.seed()
        preferences_file = self.profile / 'user.js'
        preferences_file.write_text('fixture changed after initial startup\n')
        credentials = self.profile / 'logins.json'
        credentials.write_text('fixture credentials changed\n')
        with patch('seed_profile.write_credentials') as writer:
            self.assertFalse(seed_profile(self.profile))
        writer.assert_not_called()
        self.assertEqual(
            preferences_file.read_text(), 'fixture changed after initial startup\n'
        )
        self.assertEqual(credentials.read_text(), 'fixture credentials changed\n')

    def test_existing_unmarked_profile_is_never_modified(self):
        self.profile.mkdir()
        original = self.profile / 'prefs.js'
        original.write_text('existing profile\n')
        with self.assertRaisesRegex(ValueError, 'empty disposable profile'):
            self.seed()
        self.assertEqual(original.read_text(), 'existing profile\n')
        self.assertFalse((self.profile / MARKER).exists())

    def test_symlinked_profile_is_rejected(self):
        self.profile.symlink_to(Path(self.temporary.name), target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.seed()

    def test_incomplete_or_unrecognized_marker_is_rejected(self):
        self.seed()
        (self.profile / 'logins.json').unlink()
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            self.seed()
        (self.profile / MARKER).write_text('another fixture\n')
        with self.assertRaisesRegex(ValueError, 'marker'):
            self.seed()

    def test_preferences_disable_remote_start_pages_and_telemetry(self):
        configured = preferences()
        self.assertEqual(configured['mail.server.server1.hostname'], 'mail-proxy')
        self.assertEqual(configured['mail.server.server1.port'], 3143)
        self.assertEqual(configured['mail.server.server1.authMethod'], 3)
        self.assertEqual(configured['mail.smtpserver.smtp1.hostname'], 'mail-proxy')
        self.assertEqual(configured['mail.smtpserver.smtp1.port'], 3025)
        self.assertEqual(configured['mail.smtpserver.smtp1.authMethod'], 1)
        self.assertFalse(configured['mailnews.start_page.enabled'])
        self.assertFalse(configured['datareporting.policy.dataSubmissionEnabled'])


if __name__ == '__main__':
    unittest.main()
