import os
import re
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from automation.paths import REPOSITORY_ROOT
from automation.quality import javascript, python, runner, shell, sql
from automation.quality.runner import TARGETS


def make_list(makefile, name):
    return re.search(rf'^{name} := (.*)$', makefile, re.MULTILINE)[1].split()


class QualityTargetTests(unittest.TestCase):
    def setUp(self):
        self.makefile = (REPOSITORY_ROOT / 'Makefile').read_text().replace('\\\n', ' ')

    def test_make_offers_exactly_the_runner_targets(self):
        self.assertEqual(sorted(make_list(self.makefile, 'QUALITY_TARGETS')), sorted(TARGETS))

    def test_every_language_formats_and_checks_alone(self):
        for language in ('bash', 'python', 'javascript', 'rust', 'sql'):
            with self.subTest(language=language):
                self.assertIn(f'format-{language}', TARGETS)
                self.assertIn(f'format-check-{language}', TARGETS)

    def test_rewriting_targets_use_the_writable_service(self):
        writing = make_list(self.makefile, 'WRITING_TARGETS')
        for target in TARGETS:
            if target.startswith('format') and not target.startswith('format-check'):
                with self.subTest(target=target):
                    self.assertIn(target, writing)

    def test_shfmt_options_come_from_its_configuration_file(self):
        self.assertIn('--indent', shell.shfmt_options())

    def test_tool_failures_name_the_tool_without_its_arguments(self):
        cases = {
            ('typos', '--isolated', '/workspace/a.md'): 'typos exited with status 2',
            ('ruff', 'check', '--quiet', '/workspace/a.py'): 'ruff check exited with status 2',
            ('/usr/bin/cargo', 'clippy', '--workspace'): 'cargo clippy exited with status 2',
            ('shellcheck',): 'shellcheck exited with status 2',
        }
        for command, message in cases.items():
            with self.subTest(command=command):
                self.assertEqual(runner.failure_message(subprocess.CalledProcessError(2, list(command))), message)

    def test_verbose_runs_drop_the_quiet_flags(self):
        cases = (
            (python, python.python, [Path('module.py')], 'lint', '--quiet'),
            (javascript, javascript.javascript, [Path('script.js')], 'format-check', '--log-level'),
        )
        for module, check, files, action, flag in cases:
            for verbose, present in (('', True), ('1', False)):
                with (
                    self.subTest(check=check.__name__, verbose=verbose),
                    mock.patch.dict(os.environ, {'VERBOSE': verbose}),
                    mock.patch.object(module, 'run') as run,
                ):
                    check(Path('/workspace'), files, action)
                    self.assertEqual(any(flag in call.args[0] for call in run.call_args_list), present)

    def test_verbose_sql_checks_drop_the_quiet_flag(self):
        for verbose, present in (('', True), ('1', False)):
            with (
                self.subTest(verbose=verbose),
                mock.patch.dict(os.environ, {'VERBOSE': verbose}),
                mock.patch.object(sql, 'run') as run,
            ):
                sql.sql(Path('/workspace'), [Path('query.sql')], 'lint', REPOSITORY_ROOT)
                self.assertEqual('--quiet' in run.call_args.args[0], present)


if __name__ == '__main__':
    unittest.main()
