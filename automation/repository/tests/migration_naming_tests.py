from automation.testing.guard_fixtures import GuardTestCase


class MigrationNamingTests(GuardTestCase):
    def check(self, repo):
        return self.run_guard(repo, 'check_source_naming.py', {})

    def test_accepts_four_digit_versions_and_underscore_descriptions(self):
        repo = self.repo()
        for name in [
            '0000_connector_credentials.sql',
            '0001_account_preferences.sql',
            '0012_oauth2_sessions.sql',
        ]:
            repo.write(f'server/migrations/{name}', '')
        result = self.check(repo)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_dates_and_incorrectly_padded_versions(self):
        for name in [
            '202610180001_connector_credentials.sql',
            '20261018_create_state.sql',
            '0_create_state.sql',
            '000_create_state.sql',
            '00000_create_state.sql',
            'create_state.sql',
        ]:
            with self.subTest(name=name):
                repo = self.repo()
                repo.write(f'server/migrations/{name}', '')
                result = self.check(repo)
                self.assertEqual(result.returncode, 1)
                self.assertIn(name, result.stderr)
                self.assertIn('four-digit', result.stderr)

    def test_rejects_missing_or_invalid_descriptions(self):
        for name in [
            '0000_.sql',
            '0000_123.sql',
            '0000_Create_state.sql',
            '0000_create-state.sql',
            '0000_create__state.sql',
            '0000_create_state.SQL',
        ]:
            with self.subTest(name=name):
                repo = self.repo()
                repo.write(f'server/migrations/{name}', '')
                result = self.check(repo)
                self.assertEqual(result.returncode, 1)
                self.assertIn(name, result.stderr)

    def test_rejects_duplicate_versions_across_tracked_and_untracked_files(self):
        repo = self.repo()
        repo.write('server/migrations/0000_create_state.sql', '')
        repo.commit()
        repo.write('server/migrations/0000_add_settings.sql', '')
        result = self.check(repo)
        self.assertEqual(result.returncode, 1)
        self.assertIn('duplicate migration version 0000', result.stderr)
        self.assertIn('0000_create_state.sql', result.stderr)
        self.assertIn('0000_add_settings.sql', result.stderr)

    def test_checks_missing_tracked_and_untracked_migration_names(self):
        repo = self.repo()
        tracked = 'server/migrations/20261018_create_state.sql'
        untracked = 'server/migrations/20261019_add_settings.sql'
        repo.write(tracked, '')
        repo.commit()
        (repo.root / tracked).unlink()
        repo.write(untracked, '')
        result = self.check(repo)
        self.assertEqual(result.returncode, 1)
        self.assertIn(tracked, result.stderr)
        self.assertIn(untracked, result.stderr)

    def test_does_not_apply_migration_numbering_to_other_sql_sources(self):
        repo = self.repo()
        repo.write('server/queries/count_migrations.sql', '')
        repo.write('fixtures/20261018_query.sql', '')
        result = self.check(repo)
        self.assertEqual(result.returncode, 0, result.stderr)
