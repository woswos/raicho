import fcntl
import subprocess
import tempfile
import unittest
from pathlib import Path

from automation.testing.docker_mock import DockerMock, Response

WRAPPER = Path(__file__).resolve().parents[1] / 'login.bash'
PASSWORD = 'fictional long password'


class LoginWrapperTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-login-test-')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.state = self.directory / 'state'
        self.state.mkdir(mode=0o700)

    def run_wrapper(self, operation, running='', standard_input=f'{PASSWORD}\n'):
        self.docker = DockerMock(self.directory / 'commands', [Response(('ps',), output=running)])
        result = subprocess.run(
            ['bash', str(WRAPPER), operation],
            env=self.docker.environment(
                RAICHO_PROJECT='raicho-login-test',
                RAICHO_STATE_DIRECTORY=str(self.state),
                TMPDIR=str(self.directory),
            ),
            input=standard_input,
            capture_output=True,
            text=True,
            check=False,
        )
        return result, [' '.join(command) for command in self.docker.commands()]

    def test_unknown_operations_are_rejected_before_docker(self):
        result, commands = self.run_wrapper('rotate')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(commands, [])

    def test_the_password_travels_on_standard_input_and_a_running_server_restarts(self):
        result, commands = self.run_wrapper('reset', running='container\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(commands[1].endswith('stop raicho'))
        self.assertTrue(commands[2].endswith('run --rm --no-deps -T login reset'))
        self.assertIn('-f compose.login.yaml', commands[2])
        self.assertTrue(commands[3].endswith('up -d --no-deps --wait --wait-timeout 120 raicho'))
        self.assertFalse(any(PASSWORD in command for command in commands))
        self.assertNotIn(PASSWORD, result.stdout + result.stderr)
        self.assertIn('Raicho restarted.', result.stdout)

    def test_a_stopped_server_stays_stopped(self):
        result, commands = self.run_wrapper('revoke', standard_input='')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any(' up ' in command for command in commands))
        self.assertIn('Raicho remains stopped.', result.stdout)

    def test_a_missing_password_fails_before_docker(self):
        result, commands = self.run_wrapper('init', standard_input='')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('no password on standard input', result.stderr)
        self.assertEqual(commands, [])

    def test_a_running_credential_operation_blocks_login_changes(self):
        lock = self.state / 'operation.lock'
        lock.touch(mode=0o600)
        with lock.open('a') as held:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result, commands = self.run_wrapper('status', standard_input='')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('another credential operation is running', result.stderr)
        self.assertEqual(commands, [])


if __name__ == '__main__':
    unittest.main()
