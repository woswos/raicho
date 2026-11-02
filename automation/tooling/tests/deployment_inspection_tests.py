import tempfile
import unittest
from pathlib import Path

from automation.paths import REPOSITORY_ROOT
from automation.testing.docker_mock import DockerMock
from automation.tooling.tests.deployment_tests import dry_run, run_make

COMPOSE = f"docker compose --progress quiet -p 'raicho' -f {REPOSITORY_ROOT}/compose.yaml"


class DeploymentInspectionTests(unittest.TestCase):
    def test_logs_show_every_service_or_follow_one(self):
        self.assertEqual(dry_run('deploy-logs'), f'{COMPOSE} logs --timestamps\n')
        self.assertEqual(
            dry_run('deploy-logs', SERVICE='thunderbird', FOLLOW='1'),
            f'{COMPOSE} logs --timestamps --follow thunderbird\n',
        )

    def test_restart_keeps_the_containers_and_images(self):
        commands = dry_run('deploy-restart', SERVICE='raicho')
        self.assertIn(f'deploy-restart {COMPOSE} restart raicho\n', commands)
        self.assertNotIn(' build', commands)
        self.assertNotIn(' up ', commands)

    def test_a_shell_opens_in_the_named_service(self):
        self.assertEqual(dry_run('deploy-shell', SERVICE='thunderbird'), f'{COMPOSE} exec thunderbird sh\n')

    def test_a_shell_needs_a_service(self):
        with tempfile.TemporaryDirectory() as directory:
            docker = DockerMock(Path(directory))
            result = run_make('deploy-shell', PATH=docker.environment()['PATH'])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('make deploy-shell SERVICE=thunderbird', result.stderr)
            self.assertEqual(docker.commands(), [])

    def test_health_reads_the_status_inside_the_raicho_container(self):
        commands = dry_run('deploy-health', RAICHO_COMMIT='custom')
        self.assertIn(f'{COMPOSE} exec -T raicho curl', commands)
        self.assertIn(' http://127.0.0.1:8080/api/status | ', commands)
        self.assertIn(' run --rm -T check python3 -B -m automation.tooling.deployment_health custom\n', commands)


if __name__ == '__main__':
    unittest.main()
