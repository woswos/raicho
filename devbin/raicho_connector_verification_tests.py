import os
import subprocess
import tempfile
import unittest
from pathlib import Path

WRAPPER = Path(__file__).with_name('raicho_connector.bash')


class ConnectorVerificationTests(unittest.TestCase):
    def run_verification(self, directory, check_status):
        state = directory / 'state'
        state.mkdir(mode=0o700)
        trace = directory / 'trace'
        commands = directory / 'commands'
        commands.mkdir()
        docker = commands / 'docker'
        docker.write_text(
            '#!/usr/bin/env bash\n'
            'printf "%s\\n" "${*}" >> "${MOCK_DOCKER_TRACE}"\n'
            'case " ${*} " in\n'
            '  *" credential_check "*) exit "${MOCK_CHECK_STATUS}" ;;\n'
            'esac\n'
            'exit 0\n'
        )
        docker.chmod(0o700)
        result = subprocess.run(
            ['bash', str(WRAPPER), 'verify'],
            env={
                **os.environ,
                'PATH': f'{commands}:{os.environ["PATH"]}',
                'RAICHO_PROJECT': 'raicho-verification-test',
                'RAICHO_STATE_DIRECTORY': str(state),
                'RAICHO_COMPOSE_TEST': '0',
                'MOCK_DOCKER_TRACE': str(trace),
                'MOCK_CHECK_STATUS': str(check_status),
            },
            capture_output=True,
            text=True,
            check=False,
        )
        return result, trace.read_text().splitlines()

    def test_failed_live_authentication_does_not_discard_previous_token(self):
        with tempfile.TemporaryDirectory(prefix='raicho-verification-') as temporary:
            result, commands = self.run_verification(Path(temporary), 1)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(any('credential_check' in command for command in commands))
        self.assertFalse(
            any('credential_files finish' in command for command in commands)
        )
        self.assertNotIn('Services recreated.', result.stdout)

    def test_cleanup_follows_proxy_start_and_live_verification(self):
        with tempfile.TemporaryDirectory(prefix='raicho-verification-') as temporary:
            result, commands = self.run_verification(Path(temporary), 0)
        self.assertEqual(result.returncode, 0, result.stderr)
        start = next(
            index for index, command in enumerate(commands) if ' up ' in command
        )
        verify = next(
            index
            for index, command in enumerate(commands)
            if 'credential_check' in command
        )
        finish = next(
            index
            for index, command in enumerate(commands)
            if 'credential_files finish' in command
        )
        self.assertIn('raicho connector_proxy thunderbird', commands[start])
        self.assertLess(start, verify)
        self.assertLess(verify, finish)
