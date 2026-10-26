from automation.paths import REPOSITORY_ROOT
from automation.testing.guard_fixtures import GuardTestCase

SCRIPT = 'check_schema_naming.py'
VALID_SCHEMA = """
CREATE TABLE account_preferences (
    identifier INTEGER PRIMARY KEY AUTOINCREMENT,
    theme_name TEXT NOT NULL,
    oauth2_scope TEXT
);
CREATE INDEX account_preferences_by_theme ON account_preferences (theme_name);
CREATE VIEW dark_preferences AS
    SELECT identifier FROM account_preferences WHERE theme_name = 'dark';
CREATE TRIGGER account_preferences_audit AFTER INSERT ON account_preferences
BEGIN
    SELECT 1;
END;
"""


class SchemaNamingTests(GuardTestCase):
    def check(self, migrations):
        repo = self.repo()
        for name, sql in migrations.items():
            repo.write(f'server/migrations/{name}', sql)
        return self.run_guard(repo, SCRIPT, {})

    def assert_rejected(self, result, *messages):
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertEqual(result.stdout, '')
        for message in messages:
            self.assertIn(f'FAIL: {message}', result.stderr)

    def test_repository_migrations_use_snake_case_names(self):
        result = self.run_guard_cli_root(REPOSITORY_ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('schema-naming check passed', result.stdout)

    def run_guard_cli_root(self, root):
        return self.run_command(
            [
                'python3',
                '-B',
                '-m',
                'automation.repository.check_schema_naming',
                str(root),
            ],
            root,
            {},
        )

    def test_accepts_snake_case_objects_and_skips_sqlite_internals(self):
        result = self.check({'0000_account_preferences.sql': VALID_SCHEMA})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')

    def test_accepts_a_repository_without_migrations(self):
        result = self.run_guard(self.repo(), SCRIPT, {})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_table_and_column_names_that_are_not_snake_case(self):
        result = self.check(
            {
                '0000_bad_names.sql': (
                    'CREATE TABLE accountPreferences (identifier INTEGER);\n'
                    'CREATE TABLE Settings (themeName TEXT, Upper TEXT,'
                    ' double__underscore TEXT, trailing_ TEXT, "spaced name" TEXT,'
                    ' "1column" TEXT, _leading TEXT);\n'
                )
            }
        )
        migration = 'server/migrations/0000_bad_names.sql'
        self.assert_rejected(
            result,
            f'{migration}: table accountPreferences must use snake_case',
            f'{migration}: table Settings must use snake_case',
            *(
                f'{migration}: column Settings.{column} must use snake_case'
                for column in (
                    'themeName',
                    'Upper',
                    'double__underscore',
                    'trailing_',
                    'spaced name',
                    '1column',
                    '_leading',
                )
            ),
        )

    def test_rejects_index_view_and_trigger_names_that_are_not_snake_case(self):
        result = self.check(
            {
                '0000_objects.sql': (
                    'CREATE TABLE settings (theme TEXT);\n'
                    'CREATE INDEX settingsByTheme ON settings (theme);\n'
                    'CREATE VIEW "Dark Settings" AS SELECT theme FROM settings;\n'
                    'CREATE TRIGGER settings__audit AFTER INSERT ON settings\n'
                    'BEGIN SELECT 1; END;\n'
                )
            }
        )
        migration = 'server/migrations/0000_objects.sql'
        self.assert_rejected(
            result,
            f'{migration}: index settingsByTheme must use snake_case',
            f'{migration}: view Dark Settings must use snake_case',
            f'{migration}: trigger settings__audit must use snake_case',
        )

    def test_reports_the_migration_that_introduces_each_name(self):
        result = self.check(
            {
                '0000_settings.sql': 'CREATE TABLE settings (theme TEXT);\n',
                '0001_settings_owner.sql': (
                    'ALTER TABLE settings ADD COLUMN ownerName TEXT;\n'
                ),
            }
        )
        self.assert_rejected(
            result,
            'server/migrations/0001_settings_owner.sql: column settings.ownerName'
            ' must use snake_case',
        )
        self.assertNotIn('0000_settings.sql', result.stderr)

    def test_rejects_a_migration_that_cannot_be_applied(self):
        result = self.check(
            {
                '0000_settings.sql': 'CREATE TABLE settings (theme TEXT);\n',
                '0001_broken.sql': 'ALTER TABLE missing ADD COLUMN theme TEXT;\n',
            }
        )
        self.assert_rejected(
            result, 'server/migrations/0001_broken.sql: cannot apply migration'
        )
