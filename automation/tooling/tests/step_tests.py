import os
import re
import subprocess
import unittest

from automation.paths import REPOSITORY_ROOT

STEP = REPOSITORY_ROOT / 'automation/tooling/step.bash'
COLORS = {'COLOR_BLUE': '<blue>', 'COLOR_GREEN': '<green>', 'COLOR_RED': '<red>', 'COLOR_RESET': '<reset>'}


def step(target, *command, **environment):
    return subprocess.run(
        ['bash', str(STEP), target, *command],
        env={'PATH': os.environ['PATH'], **environment},
        capture_output=True,
        text=True,
        check=False,
    )


class StepTests(unittest.TestCase):
    def test_success_reports_the_start_and_the_duration(self):
        result = step('build-server', 'echo', 'output')
        self.assertEqual(result.returncode, 0)
        self.assertRegex(result.stdout, r'^building server\noutput\nbuilt server, took \d+ seconds?\n$')
        self.assertEqual(result.stderr, '')

    def test_failure_keeps_the_exit_status(self):
        result = step('test-web', 'sh', '-c', 'exit 3')
        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, 'testing web\n')
        self.assertRegex(result.stderr, r'^testing web failed after \d+ seconds?\n$')

    def test_usage_requires_a_command(self):
        result = step('build-server')
        self.assertEqual(result.returncode, 2)
        self.assertIn('Usage:', result.stderr)

    def test_each_target_family_has_its_own_wording(self):
        cases = {
            'build-extension': ('building extension', 'built extension'),
            'test-python': ('testing python', 'tested python'),
            'acceptance-mail': ('testing mail acceptance', 'tested mail acceptance'),
            'lint-rust': ('linting rust', 'linted rust'),
            'lint-repo': ('linting repository', 'linted repository'),
            'format-check-bash': ('checking bash formatting', 'checked bash formatting'),
            'format-sql': ('formatting sql', 'formatted sql'),
            'deploy-connector-init': ('running connector init', 'ran connector init'),
            'other': ('running other', 'ran other'),
        }
        for target, (started, finished) in cases.items():
            with self.subTest(target=target):
                lines = step(target, 'true').stdout.splitlines()
                self.assertEqual(lines[0], started)
                self.assertTrue(lines[1].startswith(f'{finished}, took '), lines[1])

    def test_lines_use_the_colors_make_exports(self):
        success = step('build-web', 'true', **COLORS)
        self.assertTrue(success.stdout.startswith('<blue>building web<reset>\n<green>built web, took '))
        failure = step('build-web', 'false', **COLORS)
        self.assertTrue(failure.stderr.startswith('<red>building web failed after '))

    def test_make_colors_only_xterm_terminals(self):
        def colors(terminal):
            return subprocess.run(
                [
                    'make',
                    '--no-print-directory',
                    '-f',
                    str(REPOSITORY_ROOT / 'Makefile'),
                    '--eval',
                    'print-colors: ; @printf "%s" "$$COLOR_BLUE$$COLOR_RESET"',
                    'print-colors',
                ],
                env={**os.environ, 'TERM': terminal},
                capture_output=True,
                text=True,
                check=True,
            ).stdout

        self.assertEqual(colors('dumb'), '')
        self.assertTrue(re.fullmatch(r'(\x1b[^a-zA-Z]*[a-zA-Z])+', colors('xterm-256color')))


if __name__ == '__main__':
    unittest.main()
