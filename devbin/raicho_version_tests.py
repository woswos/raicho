import os
import subprocess
import tempfile
from pathlib import Path

from raicho_changelog import (
    date_changelog,
    next_version,
    parse_description_entries,
    release_notes,
    release_section,
    requests_minor,
    unreleased_body,
)
from raicho_check_changelog import is_shipping
from raicho_cut_release import latest_release
from raicho_guard_fixtures import DEVBIN, GuardTestCase
from raicho_release_requests import numbers_in_subject
from raicho_version import (
    check_product_version,
    parse_version,
    replace_manifest_version,
    replace_workspace_version,
)

CHANGELOG = """# Changelog

Notable changes.

## [Unreleased]

### Fixed

- The status page names the build.

## [0.1.0] - 2026-01-01

### Added

- Initial diagnostics.
"""

CARGO = """[workspace.package]
version = "0.1.0"
edition = "2024"
"""

MANIFEST = """{
  "manifest_version": 2,
  "name": "Raicho Connector",
  "version": "0.1.0",
  "browser_specific_settings": {
    "gecko": { "strict_min_version": "153.0" }
  }
}
"""


class VersionTests(GuardTestCase):
    def test_product_version_is_three_numeric_components(self):
        self.assertEqual(parse_version('0.1.0'), (0, 1, 0))
        self.assertEqual(parse_version('65535.0.1'), (65535, 0, 1))
        for text in ('1.2', '01.2.3', '1.2.3-dev', 'v1.2.3', '1.2.65536'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_version(text)

    def test_version_files_stay_together(self):
        repo = self.repo()
        repo.write('Cargo.toml', CARGO)
        repo.write('extension/manifest.json', MANIFEST)
        repo.write('extension/mail_probe/manifest.json', MANIFEST)
        repo.write('extension/tests/manifest.json', MANIFEST.replace('0.1.0', '9.9.9'))
        repo.commit()
        self.assertEqual(check_product_version(repo.root), [])
        drifted = MANIFEST.replace('"version": "0.1.0"', '"version": "0.2.0"')
        repo.write('extension/manifest.json', drifted)
        failures = check_product_version(repo.root)
        self.assertEqual(len(failures), 1)
        self.assertIn('extension/manifest.json version 0.2.0', failures[0])

    def test_manifest_replacement_ignores_other_version_fields(self):
        updated = replace_manifest_version(MANIFEST, '0.2.0')
        self.assertIn('"version": "0.2.0"', updated)
        self.assertIn('"manifest_version": 2', updated)
        self.assertIn('"strict_min_version": "153.0"', updated)
        cargo = replace_workspace_version(CARGO, '0.2.0')
        self.assertIn('version = "0.2.0"', cargo)
        self.assertIn('edition = "2024"', cargo)

    def test_repository_declares_the_current_product_version(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(check_product_version(root), [])


class ChangelogTests(GuardTestCase):
    def test_description_entries_ignore_comments_placeholders_and_todos(self):
        description = """## Summary

## Changelog

<!-- ### Added
- hidden
-->

### Added | Changed | Fixed

- TODO: replace this placeholder.

### Fixed

- The diagnostics page shows the build commit
  after the version.

## Validation
"""
        parsed = parse_description_entries(description, '15')
        self.assertEqual(
            parsed,
            {
                'Fixed': [
                    '- The diagnostics page shows the build commit\n'
                    '  after the version. (#15)'
                ]
            },
        )

    def test_unreleased_text_stops_at_the_previous_release(self):
        self.assertEqual(
            unreleased_body(CHANGELOG),
            '### Fixed\n\n- The status page names the build.',
        )
        self.assertIn('Initial diagnostics.', release_notes(CHANGELOG, '0.1.0'))
        with self.assertRaises(ValueError):
            release_notes(CHANGELOG, '0.2.0')

    def test_version_bump_follows_the_entry_kind(self):
        self.assertEqual(
            next_version(None, False, True), ('0.1.0', 'the first release')
        )
        self.assertEqual(
            next_version('0.1.0', False, False),
            ('0.1.1', 'fixes and changes only'),
        )
        self.assertEqual(
            next_version('0.1.4', True, False),
            ('0.2.0', 'something was added or removed'),
        )
        self.assertEqual(
            next_version('0.9.1', False, True), ('1.0.0', 'asked for by hand')
        )
        self.assertTrue(requests_minor('### Added\n\n- A page.', {}))
        self.assertFalse(requests_minor('### Security\n\n- A fix.', {}))
        with self.assertRaises(ValueError):
            next_version('0.0.65535', False, False)

    def test_dated_changelog_keeps_hand_written_text_and_appends_entries(self):
        original = '# Changelog\n\n## [Unreleased]\n\n### Fixed\n\n- Hand written.\n'
        parsed = parse_description_entries(
            '## Changelog\n\n### Added\n\n- A new page.\n', '4'
        )
        section = release_section(unreleased_body(original), parsed)
        dated = date_changelog(original, '0.2.0', '2026-10-18', section)
        self.assertIn('## [Unreleased]\n\n## [0.2.0] - 2026-10-18\n', dated)
        self.assertIn('- Hand written.', dated)
        self.assertIn('- A new page. (#4)', dated)
        self.assertTrue(dated.endswith('\n'))

    def test_highest_tag_wins_over_tag_order(self):
        repo = self.repo()
        repo.write('README.md', 'base\n')
        repo.commit()
        repo.git('tag', 'v0.2.0')
        repo.git('tag', 'v0.10.0')
        repo.git('tag', 'v1')
        self.assertEqual(latest_release(repo.root), '0.10.0')
        self.assertEqual(numbers_in_subject('feat: add status (#12)'), ['12'])
        self.assertEqual(
            numbers_in_subject('Merge pull request #8 from example/branch'),
            ['8'],
        )

    def test_cut_release_dates_the_changelog_without_committing(self):
        repo = self.prepare_release()
        preview = self.cut(repo)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertIn('Next version: 0.1.1', preview.stdout)
        self.assertIn('Nothing was written', preview.stdout)
        self.assertIn('version = "0.1.0"', (repo.root / 'Cargo.toml').read_text())

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'output.txt'
            written = self.cut(repo, '--write', extra={'GITHUB_OUTPUT': str(output)})
            self.assertEqual(written.returncode, 0, written.stderr)
            self.assertIn(
                'released=true\nversion=0.1.1\ntag=v0.1.1\n', output.read_text()
            )
        changelog = (repo.root / 'CHANGELOG.md').read_text()
        self.assertIn('## [0.1.1] - ', changelog)
        self.assertIn('## [Unreleased]\n', changelog)
        self.assertIn('version = "0.1.1"', (repo.root / 'Cargo.toml').read_text())
        manifest = (repo.root / 'extension/manifest.json').read_text()
        self.assertIn('"version": "0.1.1"', manifest)
        status = subprocess.run(
            ['git', 'status', '--short'],
            cwd=repo.root,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            status.stdout,
            ' M CHANGELOG.md\n M Cargo.lock\n M Cargo.toml\n M extension/manifest.json\n',
        )

    def test_empty_unreleased_is_not_a_failure(self):
        repo = self.prepare_release(unreleased='')
        result = self.cut(repo, '--write')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('nothing to release', result.stdout)
        self.assertNotIn('## [0.1.1]', (repo.root / 'CHANGELOG.md').read_text())

    def test_added_entry_bumps_the_minor_version(self):
        repo = self.prepare_release(unreleased='### Added\n\n- A page.\n')
        result = self.cut(repo, '--write')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('## [0.2.0] - ', (repo.root / 'CHANGELOG.md').read_text())

    def test_major_bump_stays_manual(self):
        repo = self.prepare_release(unreleased='### Changed\n\n- A new contract.\n')
        result = self.cut(repo, '--write', '--major')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('## [1.0.0] - ', (repo.root / 'CHANGELOG.md').read_text())
        self.assertIn('version = "1.0.0"', (repo.root / 'Cargo.toml').read_text())

    def prepare_release(self, unreleased='### Fixed\n\n- A correction.\n'):
        repo = self.repo()
        body = '' if not unreleased else f'\n{unreleased}'
        repo.write(
            'CHANGELOG.md',
            f'# Changelog\n\n## [Unreleased]\n{body}\n## [0.1.0] - 2026-01-01\n\n'
            '### Added\n\n- Initial diagnostics.\n',
        )
        repo.write('Cargo.toml', '[workspace]\nmembers = ["server"]\n\n' + CARGO)
        repo.write(
            'server/Cargo.toml',
            '[package]\nname = "raicho-server"\nversion.workspace = true\n',
        )
        repo.write(
            'Cargo.lock',
            'version = 4\n\n[[package]]\nname = "raicho-server"\nversion = "0.1.0"\n',
        )
        repo.write('extension/manifest.json', MANIFEST)
        repo.commit()
        repo.git('tag', 'v0.1.0')
        return repo

    def cut(self, repo, *arguments, extra=None):
        environment = os.environ.copy()
        for name in ('GITHUB_REPOSITORY', 'GITHUB_TOKEN', 'GH_TOKEN', 'GITHUB_OUTPUT'):
            environment.pop(name, None)
        if extra:
            environment.update(extra)
        return subprocess.run(
            [
                'python3',
                '-B',
                str(DEVBIN / 'raicho_cut_release.py'),
                *arguments,
                str(repo.root),
            ],
            cwd=repo.root,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )


class ChangelogGuardTests(GuardTestCase):
    def test_shipping_paths_are_the_running_product(self):
        self.assertTrue(is_shipping('server/src/http.rs'))
        self.assertTrue(is_shipping('server/queries/read_sqlite_version.sql'))
        self.assertTrue(is_shipping('web/public/index.html'))
        self.assertTrue(is_shipping('runtime/thunderbird/supervisor.py'))
        self.assertTrue(is_shipping('extension/manifest.json'))
        self.assertFalse(is_shipping('server/tests/http.rs'))
        self.assertFalse(is_shipping('tests/thunderbird_runtime/supervisor_tests.py'))
        self.assertFalse(is_shipping('web/tests/status.test.mjs'))
        self.assertFalse(is_shipping('extension/tests/lifecycle.test.mjs'))
        self.assertFalse(is_shipping('devbin/raicho_version.py'))
        self.assertFalse(is_shipping('docs/reference/versioning.md'))
        self.assertFalse(is_shipping('containers/raicho/Dockerfile.dockerignore'))

    def test_shipping_change_requires_an_entry(self):
        repo, environment = self.shipping_change()
        result = self.run_guard(repo, 'raicho_check_pr.py', environment)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('no changelog entry', result.stderr)
        self.assertIn('server/src/main.rs', result.stderr)

    def test_description_entry_satisfies_the_guard(self):
        repo, environment = self.shipping_change()
        environment['PR_DESCRIPTION'] += (
            '\n\n## Changelog\n\n### Fixed\n\n- The status page names the build.\n'
        )
        result = self.run_guard(repo, 'raicho_check_pr.py', environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('description has an entry', result.stdout)

    def test_changelog_file_or_label_satisfies_the_guard(self):
        repo, environment = self.shipping_change()
        environment['PR_LABELS'] = 'no changelog'
        labeled = self.run_guard(repo, 'raicho_check_pr.py', environment)
        self.assertEqual(labeled.returncode, 0, labeled.stderr)
        self.assertIn('no changelog label', labeled.stdout)

        repo.write('CHANGELOG.md', '# Changelog\n\n## [Unreleased]\n\n- Noted.\n')
        repo.commit()
        environment = {
            'PR_BASE_SHA': environment['PR_BASE_SHA'],
            'PR_HEAD_SHA': repo.head(),
            'PR_DESCRIPTION': environment['PR_DESCRIPTION'],
        }
        updated = self.run_guard(repo, 'raicho_check_pr.py', environment)
        self.assertEqual(updated.returncode, 0, updated.stderr)
        self.assertIn('CHANGELOG.md was updated', updated.stdout)

    def shipping_change(self):
        repo = self.repo()
        decision = 'docs/decisions/20261018-test-decision.md'
        repo.write('README.md', 'base\n')
        repo.write(decision, '# Decision\n')
        repo.commit()
        base = repo.head()
        repo.write('server/src/main.rs', 'fn main() {}\n')
        repo.commit()
        return repo, {
            'PR_BASE_SHA': base,
            'PR_HEAD_SHA': repo.head(),
            'PR_DESCRIPTION': f'Decision: {decision}\n',
        }
