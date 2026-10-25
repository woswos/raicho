import subprocess
import tempfile
import unittest
from pathlib import Path

from automation.testing.raicho_docker_mock import DockerMock

WRAPPER = Path(__file__).resolve().parents[1] / 'raicho_connector.bash'


class ConnectorWrapperTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-wrapper-test-')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.state = self.directory / 'state'
        self.state.mkdir(mode=0o700)
        self.docker = DockerMock(self.directory / 'commands', status=1)

    def run_wrapper(self):
        return subprocess.run(
            ['bash', str(WRAPPER), 'status'],
            env=self.docker.environment(
                RAICHO_PROJECT='raicho-wrapper-test',
                RAICHO_STATE_DIRECTORY=str(self.state),
                RAICHO_COMPOSE_TEST='0',
            ),
            capture_output=True,
            text=True,
            check=False,
        )

    def test_symlink_lock_does_not_truncate_target_or_invoke_docker(self):
        sentinel = self.directory / 'sentinel'
        sentinel.write_text('preserve this content\n')
        (self.state / 'operation.lock').symlink_to(sentinel)
        result = self.run_wrapper()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(sentinel.read_text(), 'preserve this content\n')
        self.assertEqual(self.docker.commands(), [])
        self.assertIn('FAIL:', result.stderr)

    def test_unsafe_state_directory_is_rejected_before_docker(self):
        self.state.chmod(0o777)
        result = self.run_wrapper()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.docker.commands(), [])
        self.assertFalse((self.state / 'operation.lock').exists())
        self.assertIn('FAIL:', result.stderr)

    def test_existing_private_lock_content_survives_stop_failure(self):
        lock = self.state / 'operation.lock'
        lock.write_text('existing lock content\n')
        lock.chmod(0o600)
        result = self.run_wrapper()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotEqual(self.docker.commands(), [])
        self.assertEqual(lock.read_text(), 'existing lock content\n')
