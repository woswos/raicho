import shutil
import tempfile
import unittest
from pathlib import Path

from automation.paths import REPOSITORY_ROOT
from automation.testing.docker_mock import DockerMock, Response
from automation.tooling.tests.deployment_tests import make, run_make


def mock_viewer(docker):
    viewer = docker.directory / 'vncviewer'
    viewer.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$(dirname "$0")/viewer"\n')
    viewer.chmod(0o700)
    return docker.directory / 'viewer'


class DeploymentViewerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-viewer-test-')
        self.addCleanup(temporary.cleanup)
        self.state = Path(temporary.name)

    def test_the_viewer_opens_the_published_desktop(self):
        docker = DockerMock(
            self.state / 'docker', [Response(('port', 'thunderbird', '5900'), output='127.0.0.1:5901\n')], status=1
        )
        viewer = mock_viewer(docker)
        make('deploy-vnc', PATH=docker.environment()['PATH'], COMPOSE_PROJECT_NAME='second')
        self.assertEqual(viewer.read_text(), '127.0.0.1::5901\n')
        self.assertEqual(
            [' '.join(command) for command in docker.commands()],
            [f'compose --progress quiet -p second -f {REPOSITORY_ROOT}/compose.yaml port thunderbird 5900'],
        )

    def test_the_viewer_needs_the_desktop_override(self):
        for status, output in ((1, 'no port 5900/tcp for container raicho-thunderbird-1: \n'), (0, ':0\n')):
            with self.subTest(status=status, output=output):
                docker = DockerMock(
                    self.state / f'docker-{status}', [Response(('port',), status=status, output=output)]
                )
                viewer = mock_viewer(docker)
                result = run_make('deploy-vnc', PATH=docker.environment()['PATH'])
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Run make deploy-admin first.', result.stderr)
                self.assertFalse(viewer.exists())
                self.assertEqual([command[-3:] for command in docker.commands()], [['port', 'thunderbird', '5900']])

    def test_a_failed_lookup_shows_the_docker_error(self):
        error = 'failed to connect to the docker API at unix:///var/run/docker.sock\n'
        docker = DockerMock(self.state / 'docker', [Response(('port',), status=1, output=error)])
        viewer = mock_viewer(docker)
        result = run_make('deploy-vnc', PATH=docker.environment()['PATH'])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(error.strip(), result.stderr)
        self.assertIn('Could not look up the Thunderbird VNC port.', result.stderr)
        self.assertNotIn('make deploy-admin', result.stderr)
        self.assertFalse(viewer.exists())

    def test_the_viewer_must_be_installed(self):
        docker = DockerMock(self.state / 'docker', [Response(('port',), output='127.0.0.1:5900\n')])
        tools = self.state / 'tools'
        tools.mkdir()
        for name in ('make', 'python3', 'bash'):
            (tools / name).symlink_to(shutil.which(name))
        result = run_make('deploy-vnc', PATH=f'{docker.directory}:{tools}')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('make deploy-vnc needs vncviewer', result.stderr)
        self.assertEqual(docker.commands(), [])


if __name__ == '__main__':
    unittest.main()
