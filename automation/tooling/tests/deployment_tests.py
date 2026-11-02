import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from automation.paths import REPOSITORY_ROOT

SELECTION = (
    'RAICHO_TOOLING_CONTAINER',
    'RAICHO_PROJECT',
    'COMPOSE_PROJECT_NAME',
    'RAICHO_STATE_DIRECTORY',
    'RAICHO_COMMIT',
    'VERBOSE',
    'SERVICE',
    'FOLLOW',
    'TEST',
    # A Make that runs these tests passes its own command-line assignments on through these.
    'MAKEFLAGS',
    'MFLAGS',
    'MAKELEVEL',
)
CREDENTIALS_FILE = f'-f {REPOSITORY_ROOT}/compose.credentials.yaml'


def run_make(*arguments, **environment):
    host = {name: value for name, value in os.environ.items() if name not in SELECTION}
    return subprocess.run(
        ['make', '--no-print-directory', '-f', str(REPOSITORY_ROOT / 'Makefile'), *arguments],
        env=host | {'TERM': 'dumb'} | environment,
        capture_output=True,
        text=True,
    )


def make(*arguments, **environment):
    result = run_make(*arguments, **environment)
    result.check_returncode()
    return result.stdout


def dry_run(target, **environment):
    return make('-n', target, **environment)


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-deployment-test-')
        self.addCleanup(temporary.cleanup)
        self.state = Path(temporary.name)

    def test_an_unenrolled_deployment_starts_without_the_connector_token(self):
        commands = dry_run('deploy-up', RAICHO_STATE_DIRECTORY=str(self.state))
        self.assertIn(
            f"deploy-up docker compose --progress quiet -p 'raicho' -f {REPOSITORY_ROOT}/compose.yaml up", commands
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
                self.assertIn(f"RAICHO_CREDENTIAL_DIRECTORY='{credentials}' ", commands)
                self.assertIn(CREDENTIALS_FILE, commands)
        self.assertNotIn(CREDENTIALS_FILE, dry_run('deploy-down', RAICHO_STATE_DIRECTORY=str(self.state)))

    def test_enrolling_earlier_in_the_same_run_mounts_the_token(self):
        commands = make(
            '-n',
            '--eval',
            'enroll-fixture: ; +@mkdir -p $(DEPLOYMENT_CREDENTIALS)',
            'enroll-fixture',
            'deploy-up',
            RAICHO_STATE_DIRECTORY=str(self.state),
        )
        self.assertIn(CREDENTIALS_FILE, commands)

    def test_a_state_path_with_spaces_or_quotes_keeps_its_token(self):
        for name in ('with space', 'two  spaces', "it's"):
            with self.subTest(name=name):
                state = self.state / name
                (state / 'credentials').mkdir(parents=True)
                commands = dry_run('deploy-up', RAICHO_STATE_DIRECTORY=str(state))
                quoted = str(state / 'credentials').replace("'", "'\\''")
                self.assertIn(f"RAICHO_CREDENTIAL_DIRECTORY='{quoted}' ", commands)
                self.assertIn(CREDENTIALS_FILE, commands)

    def test_the_project_follows_the_credential_script(self):
        cases = (
            ({'RAICHO_PROJECT': 'first', 'COMPOSE_PROJECT_NAME': 'second'}, "-p 'first' "),
            ({'COMPOSE_PROJECT_NAME': 'second'}, "-p 'second' "),
            ({}, "-p 'raicho' "),
            ({'RAICHO_PROJECT': "it's"}, "-p 'it'\\''s' "),
        )
        for environment, expected in cases:
            with self.subTest(environment=environment):
                self.assertIn(expected, dry_run('deploy-down', **environment))

    def test_the_desktop_override_prints_its_address(self):
        commands = dry_run('deploy-admin', RAICHO_STATE_DIRECTORY=str(self.state))
        self.assertIn(f'-f {REPOSITORY_ROOT}/compose.admin.yaml up -d --wait', commands)
        self.assertIn('/vnc.html?autoconnect=true&resize=remote', commands)
        self.assertIn('make deploy-vnc', commands)

    def test_the_container_listing_selects_the_deployment(self):
        self.assertEqual(
            dry_run('deploy-ps', COMPOSE_PROJECT_NAME='second'),
            f"docker compose --progress quiet -p 'second' -f {REPOSITORY_ROOT}/compose.yaml ps\n",
        )

    def test_connector_targets_run_the_matching_command(self):
        for command in ('init', 'rotate', 'verify', 'status', 'revoke', 'reactivate'):
            with self.subTest(command=command):
                commands = dry_run(f'deploy-connector-{command}')
                self.assertIn(f'deploy/credentials/connector.bash {command}\n', commands)

    def test_images_record_the_checked_out_commit(self):
        self.assertRegex(dry_run('images'), re.compile(r'^RAICHO_COMMIT=[0-9a-f]{40}(-dirty)? ', re.MULTILINE))
        self.assertIn('RAICHO_COMMIT=custom ', dry_run('images', RAICHO_COMMIT='custom'))


if __name__ == '__main__':
    unittest.main()
