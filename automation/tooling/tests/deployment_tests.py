import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from automation.paths import REPOSITORY_ROOT
from automation.testing.docker_mock import DockerMock

SELECTION = (
    'RAICHO_TOOLING_CONTAINER',
    'RAICHO_PROJECT',
    'COMPOSE_PROJECT_NAME',
    'RAICHO_STATE_DIRECTORY',
    'RAICHO_COMMIT',
    'VERBOSE',
)
CREDENTIALS_FILE = f'-f {REPOSITORY_ROOT}/compose.credentials.yaml'


def make(*arguments, **environment):
    host = {name: value for name, value in os.environ.items() if name not in SELECTION}
    return subprocess.run(
        ['make', '--no-print-directory', '-f', str(REPOSITORY_ROOT / 'Makefile'), *arguments],
        env=host | {'TERM': 'dumb'} | environment,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


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
                self.assertIn(f"RAICHO_CREDENTIAL_DIRECTORY='{credentials}' ", commands)
                self.assertIn(CREDENTIALS_FILE, commands)
        self.assertNotIn(CREDENTIALS_FILE, dry_run('deploy-down', RAICHO_STATE_DIRECTORY=str(self.state)))

    def test_a_state_path_with_spaces_keeps_its_token(self):
        state = self.state / 'with space'
        (state / 'credentials').mkdir(parents=True)
        commands = dry_run('deploy-up', RAICHO_STATE_DIRECTORY=str(state))
        self.assertIn(f"RAICHO_CREDENTIAL_DIRECTORY='{state / 'credentials'}' ", commands)
        self.assertIn(CREDENTIALS_FILE, commands)

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

    def test_images_record_the_checked_out_commit(self):
        self.assertRegex(dry_run('images'), re.compile(r'^RAICHO_COMMIT=[0-9a-f]{40}(-dirty)? ', re.MULTILINE))
        self.assertIn('RAICHO_COMMIT=custom ', dry_run('images', RAICHO_COMMIT='custom'))

    def test_the_guide_covers_every_deployment_target_without_docker(self):
        docker = DockerMock(self.state / 'docker')
        guide = make('deploy', PATH=docker.environment()['PATH'])
        targets = make('--eval', 'print-targets: ; @echo $(DEPLOYMENT_TARGETS)', 'print-targets').split()
        for target in targets:
            with self.subTest(target=target):
                if target.startswith('deploy-connector-'):
                    self.assertIn(target.removeprefix('deploy-connector-'), guide)
                elif target != 'deploy':
                    self.assertIn(f'make {target} ', guide)
        self.assertIn('make deploy-connector-<command>', guide)
        self.assertTrue(guide.startswith('Raicho deployment\n'))
        self.assertNotIn('\n# ', guide)
        self.assertEqual(docker.commands(), [])

    def test_the_guide_describes_the_selected_deployment(self):
        guide = make(
            'deploy', COMPOSE_PROJECT_NAME='second', RAICHO_STATE_DIRECTORY=str(self.state), RAICHO_PORT='8081'
        )
        for line in (
            'project            second',
            f'state directory    {self.state}',
            'connector          not enrolled',
        ):
            self.assertIn(line, guide)
        self.assertIn('http://127.0.0.1:8081', guide)
        (self.state / 'credentials').mkdir()
        self.assertIn('connector          enrolled', make('deploy', RAICHO_STATE_DIRECTORY=str(self.state)))

    def test_the_guide_is_colored_only_on_xterm_terminals(self):
        (self.state / 'credentials').mkdir()
        colored = make('deploy', TERM='xterm', RAICHO_STATE_DIRECTORY=str(self.state))
        for text in ('\x1b[36mStart and stop', '\x1b[32mmake deploy-up', '\x1b[33mRAICHO_PROJECT', '\x1b[32menrolled'):
            self.assertIn(text, colored)
        self.assertNotIn('\x1b', make('deploy', RAICHO_STATE_DIRECTORY=str(self.state)))


if __name__ == '__main__':
    unittest.main()
