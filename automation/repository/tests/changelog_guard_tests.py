from automation.repository.check_changelog import is_shipping
from automation.testing.guard_fixtures import GuardTestCase

GATEWAY_PATHS = ('deploy/gateway/nginx.conf', 'deploy/gateway/Dockerfile')


class ChangelogGuardTests(GuardTestCase):
    def test_shipping_paths_are_the_running_product(self):
        self.assertTrue(is_shipping('server/src/http.rs'))
        self.assertTrue(is_shipping('server/queries/read_sqlite_version.sql'))
        self.assertTrue(is_shipping('web/public/index.html'))
        self.assertTrue(is_shipping('web/src/status_validator_generated.js'))
        self.assertTrue(is_shipping('deploy/thunderbird/supervisor.py'))
        for path in GATEWAY_PATHS:
            with self.subTest(path=path):
                self.assertTrue(is_shipping(path))
        self.assertTrue(is_shipping('deploy/credentials/connector.bash'))
        self.assertTrue(is_shipping('deploy/raicho/Dockerfile'))
        self.assertTrue(is_shipping('extension/manifest.json'))
        self.assertTrue(is_shipping('protocol/typescript/src/decode_frame.ts'))
        self.assertTrue(is_shipping('protocol/typescript/src/validator_generated.js'))
        self.assertFalse(is_shipping('protocol/typescript/tests/contract.test.mjs'))
        self.assertFalse(is_shipping('server/tests/http.rs'))
        self.assertFalse(is_shipping('deploy/thunderbird/tests/supervisor_tests.py'))
        self.assertFalse(is_shipping('deploy/thunderbird/tests/fixture.py'))
        self.assertFalse(is_shipping('deploy/gateway/tests/nginx.conf'))
        self.assertFalse(is_shipping('deploy/gateway/tests/fixture.conf'))
        self.assertFalse(is_shipping('deploy/credentials/tests/wrapper_tests.py'))
        self.assertFalse(is_shipping('mailprobe/src/dispatcher.ts'))
        self.assertFalse(is_shipping('mailprobe/manifest.json'))
        self.assertFalse(is_shipping('web/tests/status.test.mjs'))
        self.assertFalse(is_shipping('extension/tests/lifecycle.test.mjs'))
        self.assertFalse(is_shipping('automation/release/version.py'))
        self.assertFalse(is_shipping('docs/reference/versioning.md'))
        self.assertFalse(is_shipping('deploy/raicho/Dockerfile.dockerignore'))
        self.assertFalse(is_shipping('deploy/gateway/Dockerfile.dockerignore'))

    def test_shipping_change_requires_an_entry(self):
        repo, environment = self.shipping_change()
        result = self.run_guard(repo, 'check_pr.py', environment)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('no changelog entry', result.stderr)
        self.assertIn('server/src/main.rs', result.stderr)

    def test_description_entry_satisfies_the_guard(self):
        repo, environment = self.shipping_change()
        environment['PR_DESCRIPTION'] += (
            '\n\n## Changelog\n\n### Fixed\n\n- The status page names the build.\n'
        )
        result = self.run_guard(repo, 'check_pr.py', environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('description has an entry', result.stdout)

    def test_gateway_changes_require_an_entry(self):
        for path in GATEWAY_PATHS:
            with self.subTest(path=path):
                repo, environment = self.shipping_change(path)
                result = self.run_guard(repo, 'check_pr.py', environment)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('no changelog entry', result.stderr)
                self.assertIn(path, result.stderr)

    def test_description_entry_satisfies_gateway_changes(self):
        for path in GATEWAY_PATHS:
            with self.subTest(path=path):
                repo, environment = self.shipping_change(path)
                environment['PR_DESCRIPTION'] += (
                    '\n\n## Changelog\n\n### Fixed\n\n- Update the connector gateway.\n'
                )
                result = self.run_guard(repo, 'check_pr.py', environment)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('description has an entry', result.stdout)

    def test_changelog_file_or_label_satisfies_the_guard(self):
        repo, environment = self.shipping_change()
        environment['PR_LABELS'] = 'no changelog'
        labeled = self.run_guard(repo, 'check_pr.py', environment)
        self.assertEqual(labeled.returncode, 0, labeled.stderr)
        self.assertIn('no changelog label', labeled.stdout)

        repo.write('CHANGELOG.md', '# Changelog\n\n## [Unreleased]\n\n- Noted.\n')
        repo.commit()
        environment = {
            'PR_BASE_SHA': environment['PR_BASE_SHA'],
            'PR_HEAD_SHA': repo.head(),
            'PR_DESCRIPTION': environment['PR_DESCRIPTION'],
        }
        updated = self.run_guard(repo, 'check_pr.py', environment)
        self.assertEqual(updated.returncode, 0, updated.stderr)
        self.assertIn('CHANGELOG.md was updated', updated.stdout)

    def shipping_change(self, path='server/src/main.rs'):
        repo = self.repo()
        decision = 'docs/decisions/20261018-test-decision.md'
        repo.write('README.md', 'base\n')
        repo.write(decision, '# Decision\n')
        repo.commit()
        base = repo.head()
        repo.write(path, 'fn main() {}\n')
        repo.commit()
        return repo, {
            'PR_BASE_SHA': base,
            'PR_HEAD_SHA': repo.head(),
            'PR_DESCRIPTION': f'Decision: {decision}\n',
        }
