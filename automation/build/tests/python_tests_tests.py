import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from automation.build.python_tests import summary
from automation.paths import REPOSITORY_ROOT

PASSING = 'import unittest\n\n\nclass Passing(unittest.TestCase):\n    def test_passes(self):\n        pass\n'
FAILING = 'import unittest\n\n\nclass Failing(unittest.TestCase):\n    def test_fails(self):\n        self.fail("broken on purpose")\n'


class PythonTestsSummaryTests(unittest.TestCase):
    def test_counts_passed_tests_and_names_the_suite_directory(self):
        self.assertEqual(summary('.', 263, 0), 'Python: 263 tests passed')
        self.assertEqual(
            summary('automation/quality/tests', 27, 2),
            'Python: 25 tests passed, 2 skipped in automation/quality/tests',
        )


class PythonTestsRunnerTests(unittest.TestCase):
    def run_suite(self, **modules):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / 'sample'
            package.mkdir()
            (package / '__init__.py').write_text('')
            for name, source in modules.items():
                (package / f'{name}_check.py').write_text(source)
            return subprocess.run(
                [sys.executable, '-B', '-m', 'automation.build.python_tests', 'sample', '*_check.py'],
                cwd=directory,
                env=os.environ | {'PYTHONPATH': str(REPOSITORY_ROOT)},
                capture_output=True,
                text=True,
                check=False,
            )

    def test_modules_in_separate_workers_add_up(self):
        result = self.run_suite(first=PASSING, second=PASSING)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, 'Python: 2 tests passed in sample\n')

    def test_one_failing_module_fails_the_run_and_prints_its_report(self):
        result = self.run_suite(first=PASSING, second=FAILING)
        self.assertEqual(result.returncode, 1)
        self.assertIn('broken on purpose', result.stdout)
        self.assertNotIn('tests passed', result.stdout)

    def test_a_module_that_cannot_import_fails_the_run(self):
        result = self.run_suite(first=PASSING, second='import missing_module_for_this_test\n')
        self.assertEqual(result.returncode, 1)
        self.assertIn('missing_module_for_this_test', result.stdout)


if __name__ == '__main__':
    unittest.main()
