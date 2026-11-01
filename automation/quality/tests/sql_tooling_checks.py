import subprocess

from automation.quality.tests.project_fixture import ProjectFixture


class SqlToolingChecks(ProjectFixture):
    def test_valid_sqlite_passes_lint_and_format_checks(self):
        self.write('nested/query.sql', 'SELECT 1 AS result;\n')
        self.check_runner('lint-sql')
        self.check_runner('format-check-sql')

    def test_parse_errors_fail_without_rewriting_sources(self):
        source = self.write('invalid.sql', 'SELECT FROM;\n')
        original = source.read_bytes()
        for target in ('lint-sql', 'format-check-sql', 'format-sql'):
            with self.subTest(target=target):
                self.check_runner(target, successful=False)
                self.assertEqual(source.read_bytes(), original)

    def test_format_check_never_modifies_sources(self):
        source = self.write('nested/query.sql', 'select 1 as result;\n')
        self.check_runner('format-check-sql', successful=False, diagnostic='query.sql')
        self.assertEqual(source.read_text(), 'select 1 as result;\n')

    def test_one_parse_failure_prevents_formatting_other_files(self):
        source = self.write('before.sql', 'select 1 as result;\n')
        self.write('after.sql', 'SELECT FROM;\n')
        self.check_runner('format-sql', successful=False)
        self.assertEqual(source.read_text(), 'select 1 as result;\n')

    def test_large_malformed_files_are_not_silently_skipped(self):
        self.write('large.sql', '-- padding\n' * 2500 + 'SELECT FROM;\n')
        self.check_runner('lint-sql', successful=False, diagnostic='PRS')
        self.check_runner('format-check-sql', successful=False)

    def test_format_is_idempotent(self):
        source = self.write('nested/query.sql', 'select 1 as result;\n')
        self.check_runner('format-sql')
        formatted = source.read_bytes()
        self.assertEqual(formatted, b'SELECT 1 AS result;\n')
        self.check_runner('format-sql')
        self.assertEqual(source.read_bytes(), formatted)
        self.check_runner('format-check-sql')
        self.check_runner('lint-sql')

    def test_lint_only_issue_is_not_rewritten_by_formatting(self):
        source = self.write('query.sql', 'SELECT * FROM settings;\n')
        original = source.read_bytes()
        self.check_runner('lint-sql', successful=False, diagnostic='AM04')
        self.check_runner('format-sql')
        self.assertEqual(source.read_bytes(), original)
        self.check_runner('format-check-sql')

    def test_local_configuration_and_ignore_files_do_not_override_scope(self):
        self.write('.sqlfluff', '[sqlfluff]\ndialect = nonexistent\n')
        self.write('.sqlfluffignore', '*.sql\n')
        self.write('nested/.sqlfluff', '[sqlfluff]\ndialect = nonexistent\n')
        self.write('nested/query.sql', 'select 1 as result;\n')
        self.check_runner('lint-sql', successful=False, diagnostic='CP01')
        self.check_runner('format-sql')
        self.check_runner('format-check-sql')

    def test_raw_templater_preserves_template_shaped_literals(self):
        source = self.write('query.sql', "SELECT '{{ unknown() }}' AS result;\n")
        original = source.read_bytes()
        self.check_runner('lint-sql')
        self.check_runner('format-sql')
        self.assertEqual(source.read_bytes(), original)

    def test_generated_and_vendor_sql_are_excluded(self):
        for directory in ('vendor', 'target', 'dist', 'assets/brand/references'):
            self.write(f'{directory}/invalid.sql', 'INVALID SQL\n')
        self.check_runner('lint-sql', diagnostic='SKIP')

    def test_git_scope_includes_untracked_sql_but_omits_ignored_files(self):
        self.write('.gitignore', 'ignored.sql\n')
        self.write('tracked.sql', 'SELECT 1 AS result;\n')
        subprocess.run(['git', 'add', 'tracked.sql'], cwd=self.root, check=True)
        self.write('ignored.sql', 'INVALID SQL\n')
        self.check_runner('lint-sql')
        self.write('untracked.sql', 'SELECT FROM;\n')
        self.check_runner('lint-sql', successful=False, diagnostic='untracked.sql')

    def test_empty_sql_scope_is_explicitly_skipped(self):
        for target in ('lint-sql', 'format-sql', 'format-check-sql'):
            with self.subTest(target=target):
                self.check_runner(target, diagnostic='SKIP')

    def test_missing_sqlfluff_cannot_look_like_an_empty_sql_scope(self):
        environment = self.git_only_environment()
        self.check_runner(
            'lint-sql',
            successful=False,
            diagnostic='sqlfluff is unavailable',
            environment=environment,
        )
