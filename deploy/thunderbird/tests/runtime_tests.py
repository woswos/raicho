import json
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from deploy.thunderbird.health_check import healthy
from deploy.thunderbird.runtime import admin_enabled, commands
from deploy.thunderbird.supervisor import Supervisor, process_identity


class RuntimeTests(unittest.TestCase):
    def test_administration_requires_explicit_true(self):
        for value in ('false', ''):
            with self.subTest(value=value):
                self.assertFalse(admin_enabled(value))
        self.assertTrue(admin_enabled('true'))
        with self.assertRaisesRegex(ValueError, 'true or false'):
            admin_enabled('yes')

    def test_default_commands_have_no_remote_access(self):
        selected = commands(False)
        self.assertEqual(list(selected), ['dbus', 'display', 'window-manager', 'thunderbird'])
        self.assertIn('-nolisten', selected['display'])
        self.assertIn('tcp', selected['display'])
        self.assertEqual(selected['thunderbird'][-2:], ['-profile', '/config/profile'])

    def test_administration_serves_vnc_to_published_ports(self):
        selected = commands(True)
        self.assertNotIn('-localhost', selected['vnc'])
        self.assertEqual(selected['vnc'][selected['vnc'].index('-rfbport') + 1], '5900')
        self.assertEqual(selected['browser-admin'][-2:], ['6080', '127.0.0.1:5900'])

    def test_process_identity_detects_exited_process(self):
        process = subprocess.Popen([sys.executable, '-c', 'pass'])
        process.wait(timeout=5)
        self.assertIsNone(process_identity(process.pid))

    def test_unexpected_successful_child_exit_fails_supervisor(self):
        with tempfile.TemporaryDirectory() as directory:
            supervisor = Supervisor(Path(directory) / 'state.json')
            supervisor.start('test-child', [sys.executable, '-c', 'pass'])
            self.assertEqual(supervisor.monitor(), 1)
            supervisor.stop()

    def test_shutdown_reaps_children_and_removes_health_state(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / 'state.json'
            supervisor = Supervisor(state_path)
            supervisor.start('test-child', [sys.executable, '-c', 'import time; time.sleep(60)'])
            supervisor.publish()
            self.assertTrue(state_path.exists())
            process = supervisor.children[0][1]
            supervisor.request_stop(signal.SIGTERM, None)
            supervisor.stop()
            self.assertIsNotNone(process.poll())
            self.assertFalse(state_path.exists())

    def test_failed_startup_does_not_publish_health_state(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / 'state.json'
            supervisor = Supervisor(state_path)
            with self.assertRaises(FileNotFoundError):
                supervisor.start('missing', ['/this-command-does-not-exist'])
            self.assertFalse(state_path.exists())

    def test_health_requires_all_children_and_responsive_display(self):

        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / 'state.json'
            identity = process_identity(os.getpid())
            state = [
                {'name': name, 'pid': os.getpid(), 'started': identity}
                for name in ('dbus', 'display', 'window-manager', 'thunderbird')
            ]
            state_path.write_text(json.dumps(state))
            with patch('deploy.thunderbird.health_check.subprocess.run') as display:
                display.return_value.returncode = 0
                self.assertTrue(healthy(state_path))
                display.return_value.returncode = 1
                self.assertFalse(healthy(state_path))
                display.return_value.returncode = 0
                state[-1]['started'] = 'stale'
                state_path.write_text(json.dumps(state))
                self.assertFalse(healthy(state_path))

    def test_missing_health_state_is_unhealthy(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertFalse(healthy(Path(directory) / 'absent.json'))


if __name__ == '__main__':
    unittest.main()
