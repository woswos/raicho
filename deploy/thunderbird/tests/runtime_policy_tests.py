import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from deploy.thunderbird.runtime import main


class RuntimePolicyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.paths = {
            '/tmp/raicho-runtime': self.root / 'runtime',
            '/opt/raicho/extension': self.root / 'extension',
            '/config/profile': self.root / 'profile',
        }
        self.supervisor = Mock()
        self.supervisor.state_path = (
            self.paths['/tmp/raicho-runtime'] / 'processes.json'
        )
        self.supervisor.monitor.return_value = 0

    def invoke(self, policy_writer):
        with (
            patch(
                'deploy.thunderbird.runtime.Path', side_effect=self.paths.__getitem__
            ),
            patch(
                'deploy.thunderbird.runtime.Supervisor', return_value=self.supervisor
            ),
            patch('deploy.thunderbird.runtime.signal.signal'),
            patch('deploy.thunderbird.runtime.write_policies', policy_writer),
            patch(
                'deploy.thunderbird.runtime.os.environ',
                {'RAICHO_ADMIN_ENABLED': 'false'},
            ),
        ):
            return main()

    def test_policy_is_prepared_before_any_child_starts(self):
        policy_writer = Mock()
        self.supervisor.start.side_effect = lambda *_arguments: (
            policy_writer.assert_called_once()
        )
        self.assertEqual(self.invoke(policy_writer), 0)
        policy_writer.assert_called_once_with(
            self.paths['/tmp/raicho-runtime'],
            self.paths['/opt/raicho/extension'],
            {'RAICHO_ADMIN_ENABLED': 'false'},
        )
        self.assertEqual(self.supervisor.start.call_count, 4)
        self.supervisor.stop.assert_called_once()

    def test_policy_failure_stops_startup_without_launching_children(self):
        policy_writer = Mock(side_effect=ValueError('Connector token is invalid.'))
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            self.assertEqual(self.invoke(policy_writer), 1)
        self.supervisor.start.assert_not_called()
        self.supervisor.publish.assert_not_called()
        self.supervisor.stop.assert_called_once()
        self.assertIn(
            'FAIL: Thunderbird startup failed: Connector token is invalid.',
            output.getvalue(),
        )


if __name__ == '__main__':
    unittest.main()
