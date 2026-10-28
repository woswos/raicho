import fcntl
import os
import stat
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

from automation.testing.docker_mock import DockerMock

WRAPPER = Path(__file__).resolve().parents[1] / 'connector.bash'

ACL_USER_OWNER = 0x01
ACL_NAMED_USER = 0x02
ACL_GROUP_OWNER = 0x04
ACL_MASK = 0x10
ACL_OTHER = 0x20
ACL_UNDEFINED_ID = 0xFFFFFFFF


def default_acl(uid):
    entries = [
        (ACL_USER_OWNER, 7, ACL_UNDEFINED_ID),
        (ACL_NAMED_USER, 7, uid),
        (ACL_GROUP_OWNER, 7, ACL_UNDEFINED_ID),
        (ACL_MASK, 7, ACL_UNDEFINED_ID),
        (ACL_OTHER, 5, ACL_UNDEFINED_ID),
    ]
    acl = b''.join(struct.pack('<HHI', *entry) for entry in entries)
    return struct.pack('<I', 2) + acl


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

    def test_lock_stays_private_under_a_default_acl(self):
        acl = default_acl(os.getuid())
        try:
            os.setxattr(self.state, 'system.posix_acl_default', acl)
        except OSError:
            self.skipTest('The test filesystem has no POSIX ACL support.')
        self.run_wrapper()
        lock = self.state / 'operation.lock'
        self.assertEqual(stat.S_IMODE(lock.stat().st_mode), 0o600)
