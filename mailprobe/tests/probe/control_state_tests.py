import tempfile
import threading
import time
import unittest
from pathlib import Path

from mailprobe.tests.probe.control_state import ControlState


class ControlStateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.state = ControlState(Path(temporary.name))
        self.session = self.state.connect('test-session', '153.5.0', '0.1.0')

    def submit(self, **options):
        self.result = None
        worker = threading.Thread(
            target=lambda: setattr(
                self, 'result', self.state.submit('inventory', {}, timeout=1, **options)
            )
        )
        worker.start()
        deadline = time.monotonic() + 1
        command = None
        while command is None and time.monotonic() < deadline:
            command = self.state.next_command(self.session)
            time.sleep(0.001)
        self.assertIsNotNone(command)
        self.addCleanup(worker.join)
        return worker, command

    def test_command_is_issued_once_and_result_correlates(self):
        worker, command = self.submit()
        self.assertIsNone(self.state.next_command(self.session))
        self.state.finish(self.session, {'id': command['id'], 'ok': True, 'result': 42})
        worker.join()
        self.assertEqual(self.result['result'], 42)

    def test_disconnect_never_replays_a_pending_command(self):
        worker, _command = self.submit()
        self.state.disconnect(self.session)
        worker.join()
        self.assertEqual(self.result['outcome'], 'unknown')
        self.state.connect('replacement', '153.5.0', '0.1.0')
        self.assertIsNone(self.state.next_command('replacement'))

    def test_dropped_result_is_unknown_without_replay(self):
        worker, command = self.submit(drop_result=True)
        keep_connection = self.state.finish(
            self.session, {'id': command['id'], 'ok': True, 'result': 'sent'}
        )
        worker.join()
        self.assertFalse(keep_connection)
        self.assertEqual(self.result['outcome'], 'unknown')

    def test_stale_session_cannot_finish_current_command(self):
        worker, command = self.submit()
        with self.assertRaises(ValueError):
            self.state.finish('stale', {'id': command['id'], 'ok': True, 'result': 42})
        self.state.disconnect(self.session)
        worker.join()

    def test_reconnection_with_same_reported_session_fences_old_socket(self):
        replacement = self.state.connect('test-session', '153.5.0', '0.1.0')
        self.assertNotEqual(replacement, self.session)
        self.state.disconnect(self.session)
        self.assertTrue(self.state.status()['connected'])
        self.assertEqual(self.state.session, replacement)

    def test_canceled_unissued_command_cannot_run_on_replacement(self):
        with self.state.condition:
            self.state.pending = {
                'command': {'id': 'not-issued'},
                'issued': False,
                'response': None,
                'drop_result': False,
            }
            replacement = self.state.connect('replacement', '153.5.0', '0.1.0')
            self.assertIsNone(self.state.next_command(replacement))
            self.assertEqual(self.state.pending['response']['outcome'], 'unknown')

    def test_disconnect_does_not_overwrite_definitive_result(self):
        with self.state.condition:
            self.state.pending = {'response': {'ok': True, 'result': 'sent'}}
            self.state.disconnect(self.session)
            self.assertEqual(
                self.state.pending['response'], {'ok': True, 'result': 'sent'}
            )


if __name__ == '__main__':
    unittest.main()
