import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from automation.build.python_suite import summary
from automation.paths import REPOSITORY_ROOT

SAMPLE = """import os
import unittest


class SampleTests(unittest.TestCase):
    def test_runs_without_the_callers_output_mode(self):
        self.assertNotIn('VERBOSE', os.environ)
"""
PASSING = 'import unittest\n\n\nclass Passing(unittest.TestCase):\n    def test_passes(self):\n        pass\n'
FAILING = 'import unittest\n\n\nclass Failing(unittest.TestCase):\n    def test_fails(self):\n        self.fail("broken on purpose")\n'


class PythonSuiteSummaryTests(unittest.TestCase):
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
                    [sys.executable, '-B', '-m', 'automation.build.python_suite', 'python'],
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
            (package / 'sample_tests.py').write_text(SAMPLE)
            for verbose, expected in (
                ('1', 'test_runs_without_the_callers_output_mode'),
                ('', 'Python: 1 tests passed'),
            ):
                with self.subTest(verbose=verbose):
                    result = subprocess.run(
                        [sys.executable, '-B', '-m', 'automation.build.python_suite', 'python'],
                        cwd=directory,
                        env=os.environ | {'PYTHONPATH': str(REPOSITORY_ROOT), 'VERBOSE': verbose},
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn(expected, result.stdout + result.stderr)


class PythonSuiteRunnerTests(unittest.TestCase):
    def run_suite(self, **modules):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / 'sample'
            package.mkdir()
            (package / '__init__.py').write_text('')
            for name, source in modules.items():
                (package / f'{name}_tests.py').write_text(source)
            return subprocess.run(
                [sys.executable, '-B', '-m', 'automation.build.python_suite', 'python'],
                cwd=directory,
                env=os.environ | {'PYTHONPATH': str(REPOSITORY_ROOT)},
                capture_output=True,
                text=True,
                check=False,
            )

    def test_modules_in_separate_workers_add_up(self):
        result = self.run_suite(first=PASSING, second=PASSING)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, 'Python: 2 tests passed\n')

    def test_one_failing_module_fails_the_run_and_prints_its_report(self):
        result = self.run_suite(first=PASSING, second=FAILING)
        self.assertEqual(result.returncode, 1)
        self.assertIn('broken on purpose', result.stdout)
        self.assertNotIn('tests passed', result.stdout)

    def test_a_module_skipped_at_import_counts_as_skipped(self):
        result = self.run_suite(first=PASSING, second='import unittest\n\nraise unittest.SkipTest("not here")\n')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, 'Python: 1 tests passed, 1 skipped\n')

    def test_tests_from_load_tests_run_as_discovered(self):
        source = (
            'import unittest\n\n\n'
            'def check():\n    pass\n\n\n'
            'def load_tests(loader, tests, pattern):\n    return unittest.TestSuite([unittest.FunctionTestCase(check)])\n'
        )
        result = self.run_suite(first=source)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, 'Python: 1 tests passed\n')

    def test_a_module_that_cannot_import_fails_the_run(self):
        result = self.run_suite(first=PASSING, second='import missing_module_for_this_test\n')
        self.assertEqual(result.returncode, 1)
        self.assertIn('missing_module_for_this_test', result.stdout)


if __name__ == '__main__':
    unittest.main()
