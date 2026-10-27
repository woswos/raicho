import fcntl
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from automation.testing.acl import set_default_acl
from automation.testing.docker_mock import DockerMock, Response

WRAPPER = Path(__file__).resolve().parents[1] / 'connector.bash'


class ConnectorWrapperTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-wrapper-test-')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.state = self.directory / 'state'
        self.state.mkdir(mode=0o700)
        self.docker = DockerMock(self.directory / 'commands', status=1)

    def run_wrapper(self, operation='status', project='raicho-wrapper-test', compose_test='0'):
        return subprocess.run(
            ['bash', str(WRAPPER), operation],
            env=self.docker.environment(
                RAICHO_PROJECT=project,
                RAICHO_STATE_DIRECTORY=str(self.state),
                RAICHO_COMPOSE_TEST=compose_test,
                TMPDIR=str(self.directory),
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

    def test_state_inside_another_deployment_is_rejected_before_docker(self):
        (self.state / 'operation.lock').write_text('')
        nested = self.state / 'credentials/nested'
        self.state = nested
        result = self.run_wrapper()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("inside another deployment's state", result.stderr)
        self.assertEqual(self.docker.commands(), [])
        self.assertFalse(nested.exists())

    def test_a_symlinked_parent_cannot_hide_another_deployment(self):
        outer = self.directory / 'outer'
        (outer / 'sub').mkdir(mode=0o700, parents=True)
        (outer / 'operation.lock').write_text('')
        link = self.directory / 'link'
        link.symlink_to(outer / 'sub')
        self.state = link / 'nested'
        result = self.run_wrapper()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("inside another deployment's state", result.stderr)
        self.assertEqual(self.docker.commands(), [])
        self.assertFalse((outer / 'sub/nested').exists())

    def test_a_held_state_lock_blocks_the_wrapper(self):
        layout = self.directory / f'raicho-state-{os.getuid()}'
        layout.mkdir(mode=0o700)
        with (layout / 'layout.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.run_wrapper()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('another credential or deploy-clean command', result.stderr)
        self.assertEqual(self.docker.commands(), [])
        self.assertFalse((self.state / 'operation.lock').exists())

    def test_the_wrapper_marks_and_checks_the_project(self):
        self.run_wrapper()
        marker = self.state / 'project'
        self.assertEqual(marker.read_text(), 'raicho-wrapper-test\n')
        marker.write_text('other\n')
        before = len(self.docker.commands())
        result = self.run_wrapper()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('belongs to project other', result.stderr)
        self.assertEqual(len(self.docker.commands()), before)

    def test_existing_private_lock_content_survives_stop_failure(self):
        lock = self.state / 'operation.lock'
        lock.write_text('existing lock content\n')
        lock.chmod(0o600)
        result = self.run_wrapper()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotEqual(self.docker.commands(), [])
        self.assertEqual(lock.read_text(), 'existing lock content\n')

    def test_new_state_stays_private_under_a_default_acl(self):
        set_default_acl(self, self.directory)
        self.state = self.directory / 'new'
        self.run_wrapper()
        self.assertEqual(stat.S_IMODE(self.state.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((self.state / 'operation.lock').stat().st_mode), 0o600)

    def verify(self, check_status):
        self.docker = DockerMock(
            self.directory / 'commands',
            [Response(('credential-check',), status=check_status)],
        )
        result = self.run_wrapper('verify')
        return result, [' '.join(command) for command in self.docker.commands()]

    def test_failed_live_authentication_does_not_discard_previous_token(self):
        result, commands = self.verify(1)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(any('credential-check' in command for command in commands))
        self.assertFalse(any('credential-files finish' in command for command in commands))
        self.assertNotIn('Services recreated.', result.stdout)

    def test_cleanup_follows_gateway_start_and_live_verification(self):
        result, commands = self.verify(0)
        self.assertEqual(result.returncode, 0, result.stderr)
        start = next(index for index, command in enumerate(commands) if ' up ' in command)
        verify = next(index for index, command in enumerate(commands) if 'credential-check' in command)
        finish = next(index for index, command in enumerate(commands) if 'credential-files finish' in command)
        self.assertIn('raicho gateway thunderbird', commands[start])
        self.assertLess(start, verify)
        self.assertLess(verify, finish)

    def test_any_test_flag_adds_the_test_overlay(self):
        self.run_wrapper(project='raicho-credentials-overlay', compose_test='2')
        commands = [' '.join(command) for command in self.docker.commands()]
        self.assertTrue(commands)
        self.assertTrue(all('automation/acceptance/runtime/compose.test.yaml' in command for command in commands))
