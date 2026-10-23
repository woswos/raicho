import os
import subprocess
import tempfile
import unittest
from pathlib import Path

WRAPPER = Path(__file__).resolve().parents[1] / 'raicho_connector.bash'


class ConnectorWrapperTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-wrapper-test-')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.state = self.directory / 'state'
        self.state.mkdir(mode=0o700)
        self.marker = self.directory / 'docker.called'
        self.commands = self.directory / 'commands'
        self.commands.mkdir()
        docker = self.commands / 'docker'
        docker.write_text(
            '#!/usr/bin/env bash\nprintf called > "${MOCK_DOCKER_MARKER}"\nexit 1\n'
        )
        docker.chmod(0o700)

    def run_wrapper(self):
        return subprocess.run(
            ['bash', str(WRAPPER), 'status'],
            env={
                **os.environ,
                'PATH': f'{self.commands}:{os.environ["PATH"]}',
                'RAICHO_PROJECT': 'raicho-wrapper-test',
                'RAICHO_STATE_DIRECTORY': str(self.state),
                'RAICHO_COMPOSE_TEST': '0',
                'MOCK_DOCKER_MARKER': str(self.marker),
            },
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
        self.assertFalse(self.marker.exists())
        self.assertIn('FAIL:', result.stderr)

    def test_unsafe_state_directory_is_rejected_before_docker(self):
        self.state.chmod(0o777)
        result = self.run_wrapper()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.marker.exists())
        self.assertFalse((self.state / 'operation.lock').exists())
        self.assertIn('FAIL:', result.stderr)

    def test_existing_private_lock_content_survives_stop_failure(self):
        lock = self.state / 'operation.lock'
        lock.write_text('existing lock content\n')
        lock.chmod(0o600)
        result = self.run_wrapper()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.marker.exists())
        self.assertEqual(lock.read_text(), 'existing lock content\n')
