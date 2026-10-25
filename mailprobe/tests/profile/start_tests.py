import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

from mailprobe.tests.profile.start import main


class StartTests(unittest.TestCase):
    def test_seeds_before_replacing_the_process_with_runtime(self):
        calls = Mock()
        with (
            patch('mailprobe.tests.profile.start.seed_profile', calls.seed),
            patch('mailprobe.tests.profile.start.os.execv', calls.execute),
        ):
            main()
        self.assertEqual(
            calls.mock_calls,
            [
                call.seed(Path('/config/profile')),
                call.execute(
                    sys.executable,
                    [sys.executable, '-B', '-m', 'thunderbird.runtime'],
                ),
            ],
        )

    def test_profile_failure_prevents_runtime_startup(self):
        with (
            patch(
                'mailprobe.tests.profile.start.seed_profile',
                side_effect=ValueError('Unexpected profile.'),
            ),
            patch('mailprobe.tests.profile.start.os.execv') as execute,
        ):
            with self.assertRaisesRegex(ValueError, 'Unexpected profile'):
                main()
        execute.assert_not_called()


if __name__ == '__main__':
    unittest.main()
