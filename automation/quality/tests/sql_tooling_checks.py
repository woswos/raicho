import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from automation.paths import REPOSITORY_ROOT

RUNNER = 'automation.quality.runner'


class SqlToolingChecks(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-sql-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def check(self, target, successful=True, diagnostic=None, environment=None):
        result = subprocess.run(
            [sys.executable, '-B', '-m', RUNNER, '--root', str(self.root), target],
            cwd=self.root,
            env={
                **os.environ,
                **(environment or {}),
                'PYTHONPATH': str(REPOSITORY_ROOT),
            },
            capture_output=True,
            text=True,
            check=False,
        )
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode == 0, successful, output)
        if diagnostic:
            self.assertIn(diagnostic, output)

    def test_valid_sqlite_passes_lint_and_format_checks(self):
        self.write('nested/query.sql', 'SELECT 1 AS result;\n')
        self.check('lint-sql')
        self.check('format-check-sql')

    def test_parse_errors_fail_without_rewriting_sources(self):
        source = self.write('invalid.sql', 'SELECT FROM;\n')
        original = source.read_bytes()
        for target in ('lint-sql', 'format-check-sql', 'format-sql'):
            with self.subTest(target=target):
                self.check(target, successful=False)
                self.assertEqual(source.read_bytes(), original)

    def test_format_check_never_modifies_sources(self):
        source = self.write('nested/query.sql', 'select 1 as result;\n')
        self.check('format-check-sql', successful=False, diagnostic='query.sql')
        self.assertEqual(source.read_text(), 'select 1 as result;\n')

    def test_one_parse_failure_prevents_formatting_other_files(self):
        source = self.write('before.sql', 'select 1 as result;\n')
        self.write('after.sql', 'SELECT FROM;\n')
        self.check('format-sql', successful=False)
        self.assertEqual(source.read_text(), 'select 1 as result;\n')

    def test_large_malformed_files_are_not_silently_skipped(self):
        self.write('large.sql', '-- padding\n' * 2500 + 'SELECT FROM;\n')
        self.check('lint-sql', successful=False, diagnostic='PRS')
        self.check('format-check-sql', successful=False)

    def test_format_is_idempotent(self):
        source = self.write('nested/query.sql', 'select 1 as result;\n')
        self.check('format-sql')
        formatted = source.read_bytes()
        self.assertEqual(formatted, b'SELECT 1 AS result;\n')
        self.check('format-sql')
        self.assertEqual(source.read_bytes(), formatted)
        self.check('format-check-sql')
        self.check('lint-sql')

    def test_lint_only_issue_is_not_rewritten_by_formatting(self):
        source = self.write('query.sql', 'SELECT * FROM settings;\n')
        original = source.read_bytes()
        self.check('lint-sql', successful=False, diagnostic='AM04')
        self.check('format-sql')
        self.assertEqual(source.read_bytes(), original)
        self.check('format-check-sql')

    def test_local_configuration_and_ignore_files_do_not_override_scope(self):
        self.write('.sqlfluff', '[sqlfluff]\ndialect = nonexistent\n')
        self.write('.sqlfluffignore', '*.sql\n')
        self.write('nested/.sqlfluff', '[sqlfluff]\ndialect = nonexistent\n')
        self.write('nested/query.sql', 'select 1 as result;\n')
        self.check('lint-sql', successful=False, diagnostic='CP01')
        self.check('format-sql')
        self.check('format-check-sql')

    def test_raw_templater_preserves_template_shaped_literals(self):
        source = self.write('query.sql', "SELECT '{{ unknown() }}' AS result;\n")
        original = source.read_bytes()
        self.check('lint-sql')
        self.check('format-sql')
        self.assertEqual(source.read_bytes(), original)

    def test_generated_and_vendor_sql_are_excluded(self):
        for directory in ('vendor', 'target', 'dist', 'assets/brand/references'):
            self.write(f'{directory}/invalid.sql', 'INVALID SQL\n')
        self.check('lint-sql', diagnostic='SKIP')

    def test_git_scope_includes_untracked_sql_but_omits_ignored_files(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.write('.gitignore', 'ignored.sql\n')
        self.write('tracked.sql', 'SELECT 1 AS result;\n')
        subprocess.run(['git', 'add', 'tracked.sql'], cwd=self.root, check=True)
        self.write('ignored.sql', 'INVALID SQL\n')
        self.check('lint-sql')
        self.write('untracked.sql', 'SELECT FROM;\n')
        self.check('lint-sql', successful=False, diagnostic='untracked.sql')

    def test_empty_sql_scope_is_explicitly_skipped(self):
        for target in ('lint-sql', 'format-sql', 'format-check-sql'):
            with self.subTest(target=target):
                self.check(target, diagnostic='SKIP')

    def test_sql_symlinks_are_rejected_without_following_them(self):
        original = self.write('vendor/original.sql', 'select 1 as result;\n')
        (self.root / 'linked.sql').symlink_to(original)
        self.check('format-sql', successful=False, diagnostic='not symlinks')
        self.assertEqual(original.read_text(), 'select 1 as result;\n')

    def test_missing_sqlfluff_cannot_look_like_an_empty_sql_scope(self):
        binaries = self.root / 'vendor'
        binaries.mkdir()
        (binaries / 'git').symlink_to(shutil.which('git'))
        environment = {**os.environ, 'PATH': str(binaries)}
        self.check(
            'lint-sql',
            successful=False,
            diagnostic='sqlfluff is unavailable',
            environment=environment,
        )
