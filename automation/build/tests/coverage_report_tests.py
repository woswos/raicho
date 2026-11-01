import contextlib
import io
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from automation.build import coverage_report
from automation.build.python_suite import SUITES
from automation.paths import REPOSITORY_ROOT
from protocol.generator.cli import NODE_REPORTER


class CoverageReportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-coverage-test-')
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name) / 'coverage'
        patcher = mock.patch.object(coverage_report, 'OUTPUT', self.output)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_node_coverage_reports_lcov_beside_the_summary(self):
        arguments = coverage_report.node_coverage('web')
        self.assertIn(NODE_REPORTER, arguments)
        self.assertIn(
            f'--test-reporter-destination={self.output / "typescript-web.info"}',
            arguments,
        )
        self.assertIn('--test-coverage-exclude=**/tests/**', arguments)

    def test_typescript_suites_build_with_source_maps(self):
        with (
            mock.patch.object(coverage_report, 'run_typescript_tests') as protocol,
            mock.patch.object(coverage_report, 'web') as web,
            mock.patch.object(coverage_report, 'extension') as extension,
        ):
            coverage_report.typescript()
        self.assertEqual(protocol.call_args.args[0], ['--sourceMap'])
        self.assertEqual(web.call_args.args[:2], (True, ['--source-map']))
        self.assertEqual(
            extension.call_args.args[:3],
            (REPOSITORY_ROOT / 'extension', True, ['--source-map']),
        )

    def test_python_coverage_follows_subprocesses_and_guard_copies(self):
        self.output.mkdir()
        with mock.patch.object(coverage_report, 'run') as run:
            coverage_report.python()
        coverage = tomllib.loads((REPOSITORY_ROOT / 'pyproject.toml').read_text())['tool']['coverage']
        self.assertEqual(coverage['run']['patch'], ['subprocess'])
        self.assertIn('/tmp/*/automation/', coverage['paths']['automation'])
        commands = [call.args[0] for call in run.call_args_list]
        for command in commands:
            self.assertIn(f'--rcfile={REPOSITORY_ROOT / "pyproject.toml"}', command)
        suites = [command for command in commands if 'run' in command]
        self.assertEqual([command[-1] for command in suites], list(SUITES))
        self.assertIn('combine', commands[-2])
        self.assertIn('lcov', commands[-1])

    def test_collect_starts_fresh_and_report_prints_the_summary(self):
        self.output.mkdir()
        (self.output / 'stale.info').write_text('stale')
        with (
            mock.patch.object(coverage_report, 'rust') as rust,
            mock.patch.object(coverage_report, 'typescript') as typescript,
            mock.patch.object(coverage_report, 'python') as python,
        ):
            coverage_report.collect()
            self.assertFalse((self.output / 'stale.info').exists())
            rust.assert_called_once_with(self.output)
            typescript.assert_called_once_with()
            python.assert_called_once_with()
            (self.output / 'web.info').write_text('SF:web/src/status.ts\nDA:1,1\nDA:2,0\nend_of_record\n')
            output = io.StringIO()
            with (
                mock.patch.object(coverage_report, 'collect'),
                contextlib.redirect_stdout(output),
            ):
                coverage_report.main()
        self.assertIn('web/src/status.ts', output.getvalue())
        self.assertIn('total', output.getvalue())


if __name__ == '__main__':
    unittest.main()
