import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from automation.output import quiet
from automation.paths import REPOSITORY_ROOT

SAMPLE = """import os
import unittest


class SampleTests(unittest.TestCase):
    def test_runs_without_the_callers_output_mode(self):
        self.assertNotIn('VERBOSE', os.environ)
"""


class OutputTests(unittest.TestCase):
    def test_quiet_flags_apply_unless_verbose(self):
        with mock.patch.dict(os.environ, {'VERBOSE': ''}):
            self.assertEqual(quiet('--log-level', 'warn'), ['--log-level', 'warn'])
        with mock.patch.dict(os.environ, {'VERBOSE': '1'}):
            self.assertEqual(quiet('--quiet'), [])

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
