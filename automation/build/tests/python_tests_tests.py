import os
import subprocess
import sys
import tempfile
import unittest

from automation.build.python_tests import summary
from automation.paths import REPOSITORY_ROOT


class PythonTestsSummaryTests(unittest.TestCase):
    def test_counts_passed_tests_and_names_the_suite_directory(self):
        self.assertEqual(summary('.', 263, 0), 'Python: 263 tests passed')
        self.assertEqual(
            summary('automation/quality/tests', 27, 2),
            'Python: 25 tests passed, 2 skipped in automation/quality/tests',
        )

    def test_a_run_that_finds_no_tests_fails(self):
        for verbose in ('', '1'):
            with self.subTest(verbose=verbose), tempfile.TemporaryDirectory() as directory:
                result = subprocess.run(
                    [sys.executable, '-B', '-m', 'automation.build.python_tests', '.', '*_tests.py'],
                    cwd=directory,
                    env=os.environ | {'PYTHONPATH': str(REPOSITORY_ROOT), 'VERBOSE': verbose},
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn('FAIL: no tests matched', result.stderr)


if __name__ == '__main__':
    unittest.main()
