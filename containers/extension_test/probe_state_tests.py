import json
import tempfile
import unittest
from pathlib import Path

from probe_state import ProbeState, read_token


class ProbeStateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.state = ProbeState(self.root)
        self.token = read_token(self.root)
        self.probe = {
            'type': 'lifecycle_probe',
            'token': self.token,
            'extension_version': '0.1.0',
            'browser_version': '153.5.0',
            'session_id': 'e634eb33-1919-4855-b2eb-d07de4f82758',
            'sequence': 0,
        }

    def connect(self, message=None):
        return self.state.connect(
            json.dumps(message or self.probe), 'moz-extension://fixture', now=10
        )

    def test_secret_is_private_persistent_and_absent_from_observations(self):
        self.assertEqual(len(self.token), 64)
        self.assertEqual((self.root / 'token').stat().st_mode & 0o777, 0o600)
        self.assertEqual(read_token(self.root), self.token)
        self.connect()
        saved = (self.root / 'observations.json').read_text()
        self.assertNotIn(self.token, saved)
        self.assertNotIn('token', saved)

    def test_heartbeat_records_metadata_and_contiguous_sequence(self):
        session = self.connect()
        heartbeat = self.probe | {'type': 'lifecycle_heartbeat', 'sequence': 1}
        del heartbeat['token']
        self.state.heartbeat(session, json.dumps(heartbeat), now=20)
        observation = json.loads((self.root / 'observations.json').read_text())
        recorded = observation['sessions'][0]
        self.assertEqual(recorded['heartbeat_count'], 1)
        self.assertEqual(recorded['last_seen'], 20)
        self.assertEqual(recorded['first_seen'], 10)
        self.assertEqual(recorded['origin'], 'moz-extension://fixture')

    def test_invalid_authentication_metadata_and_mail_fields_are_rejected(self):
        invalid_messages = [
            self.probe | {'token': '0' * 64},
            self.probe | {'subject': 'private mail'},
            self.probe | {'extension_version': 'secret'},
            self.probe | {'session_id': 'not-an-id'},
            self.probe | {'sequence': False},
            self.probe | {'sequence': 1},
            self.probe | {'type': 'lifecycle_heartbeat'},
        ]
        for message in invalid_messages:
            with self.subTest(message=message), self.assertRaises(ValueError):
                self.connect(message)
        self.assertEqual(self.state.snapshot()['sessions'], [])

    def test_bad_json_and_oversized_frames_are_rejected(self):
        for message in ['{', '[]', 'null', 'x' * 4097]:
            with self.subTest(message=message[:20]), self.assertRaises(ValueError):
                self.state.connect(message, None)

    def test_messages_require_utf8(self):
        payload = json.dumps(self.probe)
        for encoding in ['utf-16', 'utf-32']:
            with self.subTest(encoding=encoding), self.assertRaises(ValueError):
                self.state.connect(payload.encode(encoding), None)

    def test_reconnects_preserve_background_identity_and_first_observation(self):
        self.connect()
        self.connect()
        session = self.state.snapshot()['sessions'][0]
        self.assertEqual(session['connection_count'], 2)
        self.assertEqual(session['first_seen'], 10)
        with self.assertRaises(ValueError):
            self.connect(self.probe | {'extension_version': '0.2.0'})

    def test_heartbeat_identity_changes_are_rejected(self):
        session = self.connect()
        heartbeat = self.probe | {'type': 'lifecycle_heartbeat', 'sequence': 1}
        del heartbeat['token']
        for change in [
            {'extension_version': '0.2.0'},
            {'sequence': 3},
            {'sequence': True},
            {'token': self.token},
        ]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.state.heartbeat(session, json.dumps(heartbeat | change))

    def test_unexpected_origin_cannot_put_credentials_into_observations(self):
        with self.assertRaises(ValueError):
            self.state.connect(json.dumps(self.probe), 'https://host/?token=secret')


if __name__ == '__main__':
    unittest.main()
