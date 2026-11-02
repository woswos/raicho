import os
import shlex
import shutil
import tempfile
import unittest
from pathlib import Path

from automation.paths import REPOSITORY_ROOT
from automation.tooling.tests.deployment_tests import make, run_make

LOOKUP = f'compose --progress quiet -p raicho -f {REPOSITORY_ROOT}/compose.yaml port thunderbird 5900'


def mock_command(path, body):
    path.write_text(f'#!/bin/sh\n{body}')
    path.chmod(0o700)


class DeploymentViewerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-viewer-test-')
        self.addCleanup(temporary.cleanup)
        self.tools = Path(temporary.name)
        mock_command(self.tools / 'vncviewer', 'printf "%s\\n" "$@" > "$(dirname "$0")/viewer"\n')

    def mock_docker(self, stdout='', stderr='', status=0):
        mock_command(
            self.tools / 'docker',
            'echo "$*" >> "$(dirname "$0")/trace"\n'
            f'printf %s {shlex.quote(stdout)}\n'
            f'printf %s {shlex.quote(stderr)} >&2\n'
            f'exit {status}\n',
        )

    def deploy_vnc(self, **environment):
        return run_make('deploy-vnc', PATH=f'{self.tools}:{os.environ["PATH"]}', **environment)

    def lookups(self):
        trace = self.tools / 'trace'
        return trace.read_text().splitlines() if trace.exists() else []

    def viewer_arguments(self):
        viewer = self.tools / 'viewer'
        return viewer.read_text() if viewer.exists() else None

    def test_the_viewer_opens_the_published_desktop(self):
        self.mock_docker(stdout='127.0.0.1:5901\n')
        make('deploy-vnc', PATH=f'{self.tools}:{os.environ["PATH"]}', COMPOSE_PROJECT_NAME='second')
        self.assertEqual(self.viewer_arguments(), '127.0.0.1::5901\n')
        self.assertEqual(self.lookups(), [LOOKUP.replace('-p raicho', '-p second')])

    def test_a_lookup_warning_stays_out_of_the_address(self):
        self.mock_docker(stdout='127.0.0.1:5901\n', stderr='WARN the variable is not set\n')
        self.assertEqual(self.deploy_vnc().returncode, 0)
        self.assertEqual(self.viewer_arguments(), '127.0.0.1::5901\n')

    def test_the_viewer_needs_the_desktop_override(self):
        cases = (
            {'stderr': 'no port 5900/tcp for container raicho-thunderbird-1: \n', 'status': 1},
            {'stdout': ':0\n'},
        )
        for case in cases:
            with self.subTest(case=case):
                (self.tools / 'trace').unlink(missing_ok=True)
                self.mock_docker(**case)
                result = self.deploy_vnc()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Run make deploy-admin first.', result.stderr)
                self.assertIsNone(self.viewer_arguments())
                self.assertEqual(self.lookups(), [LOOKUP])

    def test_a_failed_lookup_shows_the_docker_error(self):
        error = 'failed to connect to the docker API at unix:///var/run/docker.sock\n'
        self.mock_docker(stderr=error, status=1)
        result = self.deploy_vnc()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(error.strip(), result.stderr)
        self.assertIn('Could not look up the Thunderbird VNC port.', result.stderr)
        self.assertNotIn('make deploy-admin', result.stderr)
        self.assertIsNone(self.viewer_arguments())

    def test_the_viewer_must_be_installed(self):
        (self.tools / 'vncviewer').unlink()
        self.mock_docker(stdout='127.0.0.1:5900\n')
        for name in ('make', 'bash'):
            (self.tools / name).symlink_to(shutil.which(name))
        result = run_make('deploy-vnc', PATH=str(self.tools))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('make deploy-vnc needs vncviewer', result.stderr)
        self.assertEqual(self.lookups(), [])


if __name__ == '__main__':
    unittest.main()
