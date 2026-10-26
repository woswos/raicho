import os
import unittest
from unittest import mock

from automation.build.patch_coverage import comparison_base, partly_covered, totals
from automation.testing.guard_fixtures import CLEARED_ENVIRONMENT, TemporaryRepo


class PatchCoverageTests(unittest.TestCase):
    def setUp(self):
        self.repo = TemporaryRepo()
        self.addCleanup(self.repo.cleanup)
        self.repo.write('README.md', 'base\n')
        self.repo.commit()
        environment = {
            name: value
            for name, value in os.environ.items()
            if name not in CLEARED_ENVIRONMENT
        }
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
            'Diff Coverage\n'
            'server/src/http.rs (100%)\n'
            'server/src/cli.rs (65.9%): Missing lines 35,49\n'
            'Coverage: 92%\n'
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


if __name__ == '__main__':
    unittest.main()
