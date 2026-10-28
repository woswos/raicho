import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from automation.build.python_tests import summary
from automation.paths import REPOSITORY_ROOT

SAMPLE = """import os
import unittest


class SampleTests(unittest.TestCase):
    def test_runs_without_the_callers_output_mode(self):
        self.assertNotIn('VERBOSE', os.environ)
"""


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

    def test_verbose_python_tests_list_each_test_without_passing_the_mode_on(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / 'sample'
            package.mkdir()
            (package / '__init__.py').write_text('')
            (package / 'sample_check.py').write_text(SAMPLE)
            for verbose, expected in (
                ('1', 'test_runs_without_the_callers_output_mode'),
                ('', 'Python: 1 tests passed'),
            ):
                with self.subTest(verbose=verbose):
                    result = subprocess.run(
                        [sys.executable, '-B', '-m', 'automation.build.python_tests', 'sample', '*_check.py'],
                        cwd=directory,
                        env=os.environ | {'PYTHONPATH': str(REPOSITORY_ROOT), 'VERBOSE': verbose},
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn(expected, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
