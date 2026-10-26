import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from automation.paths import REPOSITORY_ROOT

SELECTION = ('RAICHO_TOOLING_CONTAINER', 'RAICHO_PROJECT', 'COMPOSE_PROJECT_NAME', 'RAICHO_STATE_DIRECTORY', 'VERBOSE')
CREDENTIALS_FILE = f'-f {REPOSITORY_ROOT}/compose.credentials.yaml'


def dry_run(target, **environment):
    host = {name: value for name, value in os.environ.items() if name not in SELECTION}
    return subprocess.run(
        ['make', '--no-print-directory', '-n', '-f', str(REPOSITORY_ROOT / 'Makefile'), target],
        env=host | environment,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-deployment-test-')
        self.addCleanup(temporary.cleanup)
        self.state = Path(temporary.name)

    def test_an_unenrolled_deployment_starts_without_the_connector_token(self):
        commands = dry_run('deploy-up', RAICHO_STATE_DIRECTORY=str(self.state))
        self.assertIn(
            f'deploy-up docker compose --progress quiet -p raicho -f {REPOSITORY_ROOT}/compose.yaml up', commands
        )
        self.assertNotIn('compose.credentials.yaml', commands)
        self.assertNotIn('RAICHO_CREDENTIAL_DIRECTORY', commands)
        self.assertIn('compose.yaml build', commands)

    def test_an_enrolled_deployment_always_mounts_its_token(self):
        credentials = self.state / 'credentials'
        credentials.mkdir()
        for target in ('deploy-up', 'deploy-admin'):
            with self.subTest(target=target):
                commands = dry_run(target, RAICHO_STATE_DIRECTORY=str(self.state))
                self.assertIn(f'RAICHO_CREDENTIAL_DIRECTORY={credentials} ', commands)
                self.assertIn(CREDENTIALS_FILE, commands)
        self.assertNotIn(CREDENTIALS_FILE, dry_run('deploy-down', RAICHO_STATE_DIRECTORY=str(self.state)))

    def test_the_project_follows_the_credential_script(self):
        cases = (
            ({'RAICHO_PROJECT': 'first', 'COMPOSE_PROJECT_NAME': 'second'}, '-p first '),
            ({'COMPOSE_PROJECT_NAME': 'second'}, '-p second '),
            ({}, '-p raicho '),
        )
        for environment, expected in cases:
            with self.subTest(environment=environment):
                self.assertIn(expected, dry_run('deploy-down', **environment))

    def test_the_desktop_override_prints_its_address(self):
        commands = dry_run('deploy-admin', RAICHO_STATE_DIRECTORY=str(self.state))
        self.assertIn(f'-f {REPOSITORY_ROOT}/compose.admin.yaml up -d --wait', commands)
        self.assertIn('/vnc.html?autoconnect=true&resize=remote', commands)

    def test_connector_targets_run_the_matching_command(self):
        for command in ('init', 'rotate', 'verify', 'status', 'revoke', 'reactivate'):
            with self.subTest(command=command):
                commands = dry_run(f'deploy-connector-{command}')
                self.assertIn(f'deploy/credentials/connector.bash {command}\n', commands)


if __name__ == '__main__':
    unittest.main()
