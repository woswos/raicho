import os
import unittest
from unittest import mock

from automation.output import quiet


class OutputTests(unittest.TestCase):
    def test_quiet_flags_apply_unless_verbose(self):
        with mock.patch.dict(os.environ, {'VERBOSE': ''}):
            self.assertEqual(quiet('--log-level', 'warn'), ['--log-level', 'warn'])
        with mock.patch.dict(os.environ, {'VERBOSE': '1'}):
            self.assertEqual(quiet('--quiet'), [])


if __name__ == '__main__':
    unittest.main()
