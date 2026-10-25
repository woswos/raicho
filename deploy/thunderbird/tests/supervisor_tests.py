import signal
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from deploy.thunderbird.supervisor import Supervisor


class ShutdownTests(unittest.TestCase):
    def test_mail_stops_first_and_other_children_share_a_deadline(self):
        elapsed = [0]
        killed = set()
        signals = []

        def record_signal(process_id, signal_number):
            signals.append((process_id, signal_number))
            if signal_number == signal.SIGKILL:
                killed.add(process_id)

        def process_for(process_id):
            process = Mock(pid=process_id)
            process.poll.return_value = None

            def wait(timeout=None):
                if process_id in killed:
                    return 0
                if timeout is None:
                    self.fail('A running child was waited on without a timeout.')
                elapsed[0] += timeout
                raise subprocess.TimeoutExpired(str(process_id), timeout)

            process.wait.side_effect = wait
            return process

        with tempfile.TemporaryDirectory() as directory:
            supervisor = Supervisor(Path(directory) / 'state.json')
            names = (
                'dbus',
                'display',
                'window-manager',
                'thunderbird',
                'vnc',
                'browser-admin',
            )
            supervisor.children = [
                (name, process_for(index)) for index, name in enumerate(names, 10)
            ]
            with (
                patch(
                    'deploy.thunderbird.supervisor.time.monotonic',
                    side_effect=lambda: elapsed[0],
                ),
                patch(
                    'deploy.thunderbird.supervisor.os.killpg', side_effect=record_signal
                ),
            ):
                supervisor.stop()
        self.assertEqual(signals[0], (13, signal.SIGTERM))
        self.assertLessEqual(elapsed[0], 20)
        other_terminations = [
            index
            for index, (process_id, number) in enumerate(signals)
            if process_id != 13 and number == signal.SIGTERM
        ]
        other_kills = [
            index
            for index, (process_id, number) in enumerate(signals)
            if process_id != 13 and number == signal.SIGKILL
        ]
        self.assertLess(max(other_terminations), min(other_kills))


if __name__ == '__main__':
    unittest.main()
