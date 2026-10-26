import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from automation.build import application
from automation.build.application import NODE_REPORTER, test_summary
from automation.paths import REPOSITORY_ROOT

RESULT = 'running 3 tests\n...\ntest result: ok. 3 passed; 0 failed; 0 ignored\n'


class ApplicationTests(unittest.TestCase):
    def test_summarizes_every_passing_test_binary(self):
        output = (
            'running 2 tests\n..\n'
            'test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured\n\n'
            'running 0 tests\n\n'
            'test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured\n'
            'test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured\n'
        )
        self.assertEqual(test_summary(output), 'Rust: 7 tests passed in 3 test binaries')

    def test_verbose_cargo_test_streams_its_output(self):
        with mock.patch.object(application, 'run') as run:
            application.cargo_test(['--locked'], env={'CARGO_TERM_QUIET': 'false'})
        run.assert_called_once_with(['cargo', 'test', '--locked'], env={'CARGO_TERM_QUIET': 'false'})

    def test_quiet_cargo_test_prints_only_its_summary(self):
        completed = subprocess.CompletedProcess([], 0, stdout=RESULT)
        output = io.StringIO()
        with (
            mock.patch.object(application.subprocess, 'run', return_value=completed),
            contextlib.redirect_stdout(output),
        ):
            application.cargo_test([], env={'CARGO_TERM_QUIET': 'true'})
        self.assertEqual(output.getvalue(), 'Rust: 3 tests passed in 1 test binaries\n')

    def test_quiet_cargo_test_failure_prints_everything(self):
        completed = subprocess.CompletedProcess([], 101, stdout='panicked at x\n')
        output = io.StringIO()
        with (
            mock.patch.object(application.subprocess, 'run', return_value=completed),
            contextlib.redirect_stdout(output),
            self.assertRaises(subprocess.CalledProcessError),
        ):
            application.cargo_test([], env={'CARGO_TERM_QUIET': 'true'})
        self.assertEqual(output.getvalue(), 'panicked at x\n')

    def test_extension_builds_then_tests_with_the_reporter(self):
        with mock.patch.object(application, 'run') as run:
            application.extension(REPOSITORY_ROOT / 'extension', testing=True)
        build, tests = run.call_args_list
        self.assertEqual(build.args[0][:2], ['node', str(REPOSITORY_ROOT / 'extension/build.mjs')])
        self.assertEqual(tests.args[0][:3], ['node', '--test', NODE_REPORTER])
        self.assertIn('RAICHO_EXTENSION_BUILD_DIR', tests.kwargs['env'])

    def test_an_extension_without_tests_fails(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            mock.patch.object(application, 'run'),
            self.assertRaisesRegex(ValueError, 'No extension tests'),
        ):
            application.extension(Path(directory), testing=True)

    def test_web_builds_then_tests_with_the_reporter(self):
        with mock.patch.object(application, 'run') as run:
            application.web(testing=True)
        build, tests = run.call_args_list
        self.assertEqual(build.args[0][:2], ['node', str(REPOSITORY_ROOT / 'web/build.mjs')])
        self.assertEqual(tests.args[0][:3], ['node', '--test', NODE_REPORTER])
        self.assertIn('RAICHO_WEB_BUILD_DIR', tests.kwargs['env'])

    def test_each_target_runs_its_build_or_suite(self):
        expectations = {
            'build-server': (
                'run',
                (['cargo', 'build', '--workspace', '--all-targets', '--locked'],),
                {},
            ),
            'test-server': (
                'cargo_test',
                (['--workspace', '--all-targets', '--locked'],),
                {},
            ),
            'build-extension': (
                'extension',
                (REPOSITORY_ROOT / 'extension',),
                {'testing': False},
            ),
            'test-extension': (
                'extension',
                (REPOSITORY_ROOT / 'extension',),
                {'testing': True},
            ),
            'test-mailprobe': (
                'extension',
                (REPOSITORY_ROOT / 'mailprobe',),
                {'testing': True},
            ),
            'build-web': ('web', (), {'testing': False}),
            'test-web': ('web', (), {'testing': True}),
        }
        for target, (name, arguments, keywords) in expectations.items():
            with (
                self.subTest(target=target),
                mock.patch.object(sys, 'argv', ['application', target]),
                mock.patch.object(application, name) as called,
            ):
                application.main()
                called.assert_called_once_with(*arguments, **keywords)


if __name__ == '__main__':
    unittest.main()
