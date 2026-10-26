import contextlib
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from automation.build import patch_coverage
from automation.build.patch_coverage import comparison_base, partly_covered, totals
from automation.testing.guard_fixtures import CLEARED_ENVIRONMENT, TemporaryRepo


class PatchCoverageTests(unittest.TestCase):
    def setUp(self):
        self.repo = TemporaryRepo()
        self.addCleanup(self.repo.cleanup)
        self.repo.write('README.md', 'base\n')
        self.repo.commit()
        environment = {name: value for name, value in os.environ.items() if name not in CLEARED_ENVIRONMENT}
        patcher = mock.patch.dict(os.environ, environment, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_compares_against_the_pull_request_base(self):
        base = self.repo.head()
        self.repo.write('README.md', 'change\n')
        self.repo.commit()
        with mock.patch.dict(os.environ, {'PR_BASE_SHA': base}):
            self.assertEqual(comparison_base(self.repo.root), base)

    def test_reports_only_files_with_uncovered_lines(self):
        report = (
            'Diff Coverage\nserver/src/http.rs (100%)\nserver/src/cli.rs (65.9%): Missing lines 35,49\nCoverage: 92%\n'
        )
        self.assertEqual(
            partly_covered(report),
            'Diff Coverage\nserver/src/cli.rs (65.9%): Missing lines 35,49\nCoverage: 92%\n',
        )

    def test_a_passing_gate_prints_only_its_totals(self):
        report = (
            'Diff Coverage\n'
            'server/src/cli.rs (65.9%): Missing lines 35,49\n'
            'Total:   3096 lines\n'
            'Missing: 306 lines\n'
            'Coverage: 90%\n'
        )
        self.assertEqual(
            totals(report),
            'Total:   3096 lines\nMissing: 306 lines\nCoverage: 90%\n',
        )

    def test_requires_a_base_without_origin_main(self):
        with self.assertRaisesRegex(ValueError, 'PR_BASE_SHA'):
            comparison_base(self.repo.root)


class PatchCoverageMainTests(unittest.TestCase):
    REPORT = (
        'server/src/http.rs (100%)\n'
        'server/src/cli.rs (65.9%): Missing lines 35,49\n'
        'Total:   10 lines\n'
        'Missing: 2 lines\n'
        'Coverage: 80%\n'
    )

    def gate(self, returncode, base='a' * 40):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        reports = Path(temporary.name)
        (reports / 'rust.info').write_text('')
        completed = subprocess.CompletedProcess([], returncode, self.REPORT, '')
        output = io.StringIO()
        base_patch = (
            mock.patch.object(patch_coverage, 'comparison_base', return_value=base)
            if base
            else mock.patch.object(patch_coverage, 'comparison_base', side_effect=ValueError('no base'))
        )
        with (
            base_patch,
            mock.patch.object(patch_coverage, 'OUTPUT', reports),
            mock.patch.object(patch_coverage, 'collect') as collect,
            mock.patch.object(patch_coverage.subprocess, 'run', return_value=completed) as run,
            contextlib.redirect_stdout(output),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            status = patch_coverage.main()
        return status, output.getvalue(), collect, run

    def test_a_passing_gate_collects_then_prints_its_totals(self):
        status, output, collect, run = self.gate(0)
        self.assertEqual(status, 0)
        collect.assert_called_once_with()
        command = run.call_args.args[0]
        self.assertIn(f'--compare-branch={"a" * 40}', command)
        self.assertIn('--fail-under=90', command)
        self.assertEqual(output, 'Total:   10 lines\nMissing: 2 lines\nCoverage: 80%\n')

    def test_a_failing_gate_lists_the_partly_covered_files(self):
        status, output, _, _ = self.gate(1)
        self.assertEqual(status, 1)
        self.assertIn('server/src/cli.rs (65.9%)', output)
        self.assertNotIn('server/src/http.rs', output)

    def test_a_missing_base_fails_before_collecting(self):
        status, _, collect, _ = self.gate(0, base=None)
        self.assertEqual(status, 1)
        collect.assert_not_called()


if __name__ == '__main__':
    unittest.main()
