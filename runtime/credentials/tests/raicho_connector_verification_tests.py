import subprocess
import tempfile
import unittest
from pathlib import Path

from automation.testing.raicho_docker_mock import DockerMock, Response

WRAPPER = Path(__file__).resolve().parents[1] / 'raicho_connector.bash'


class ConnectorVerificationTests(unittest.TestCase):
    def run_verification(self, directory, check_status):
        state = directory / 'state'
        state.mkdir(mode=0o700)
        docker = DockerMock(
            directory / 'commands',
            [Response(('credential-check',), status=check_status)],
        )
        result = subprocess.run(
            ['bash', str(WRAPPER), 'verify'],
            env=docker.environment(
                RAICHO_PROJECT='raicho-verification-test',
                RAICHO_STATE_DIRECTORY=str(state),
                RAICHO_COMPOSE_TEST='0',
            ),
            capture_output=True,
            text=True,
            check=False,
        )
        return result, [' '.join(command) for command in docker.commands()]

    def test_failed_live_authentication_does_not_discard_previous_token(self):
        with tempfile.TemporaryDirectory(prefix='raicho-verification-') as temporary:
            result, commands = self.run_verification(Path(temporary), 1)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(any('credential-check' in command for command in commands))
        self.assertFalse(
            any('credential-files finish' in command for command in commands)
        )
        self.assertNotIn('Services recreated.', result.stdout)

    def test_cleanup_follows_gateway_start_and_live_verification(self):
        with tempfile.TemporaryDirectory(prefix='raicho-verification-') as temporary:
            result, commands = self.run_verification(Path(temporary), 0)
        self.assertEqual(result.returncode, 0, result.stderr)
        start = next(
            index for index, command in enumerate(commands) if ' up ' in command
        )
        verify = next(
            index
            for index, command in enumerate(commands)
            if 'credential-check' in command
        )
        finish = next(
            index
            for index, command in enumerate(commands)
            if 'credential-files finish' in command
        )
        self.assertIn('raicho gateway thunderbird', commands[start])
        self.assertLess(start, verify)
        self.assertLess(verify, finish)
