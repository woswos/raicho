import contextlib
import io
import os
from unittest.mock import patch

from automation.release.cut_release import main
from automation.release.pull_requests import collect_entries
from automation.testing.guard_fixtures import GuardTestCase


class ReleaseCollectionTests(GuardTestCase):
    def test_skips_issue_references_and_excluded_pull_requests(self):
        with (
            patch(
                'automation.release.pull_requests.fetch_blocker',
                return_value=None,
            ),
            patch(
                'automation.release.pull_requests.pull_request_numbers',
                return_value=['1', '2', '3'],
            ),
            patch(
                'automation.release.pull_requests.github_pull_request',
                side_effect=[
                    None,
                    ('## Changelog\n\n### Added\n\n- Hidden.', ['skip-changelog']),
                    ('## Changelog\n\n### Fixed\n\n- Corrected.', []),
                ],
            ),
        ):
            entries, count = collect_entries(self.repo().root, '0.1.0')
        self.assertEqual(count, 2)
        self.assertEqual(entries, {'Fixed': ['- Corrected. (#3)']})

    def test_partial_collection_failure_leaves_release_files_unchanged(self):
        repo = self.repo()
        original = {
            'Cargo.toml': '[workspace.package]\nversion = "0.1.0"\n',
            'Cargo.lock': 'version = 4\n',
            'CHANGELOG.md': '# Changelog\n\n## [Unreleased]\n\n'
            '### Fixed\n\n- Written correction.\n',
        }
        for name, content in original.items():
            repo.write(name, content)
        output = repo.root / 'output.txt'
        errors = io.StringIO()
        with (
            patch.dict(os.environ, {'GITHUB_OUTPUT': str(output)}),
            patch(
                'automation.release.cut_release.latest_release',
                return_value='0.1.0',
            ),
            patch(
                'automation.release.pull_requests.fetch_blocker',
                return_value=None,
            ),
            patch(
                'automation.release.pull_requests.pull_request_numbers',
                return_value=['1', '2'],
            ),
            patch(
                'automation.release.pull_requests.github_pull_request',
                side_effect=[
                    ('## Changelog\n\n### Fixed\n\n- Collected correction.', []),
                    ValueError('Cannot read pull request #2: HTTP 500'),
                ],
            ),
            contextlib.redirect_stderr(errors),
        ):
            result = main(['--write', str(repo.root)])
        self.assertEqual(result, 1)
        self.assertIn('HTTP 500', errors.getvalue())
        self.assertFalse(output.exists())
        for name, content in original.items():
            self.assertEqual((repo.root / name).read_text(), content)
