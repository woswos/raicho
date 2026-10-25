from automation.repository.raicho_check_changelog import is_shipping
from automation.testing.raicho_guard_fixtures import GuardTestCase

RUST_PROTOCOL_PATHS = (
    'protocol/rust/src/decode_frame.rs',
    'protocol/rust/src/raw_json.rs',
    'protocol/rust/src/diagnostics_generated.rs',
)
PROBE_PATHS = tuple(
    f'extension/{probe}/{path}'
    for probe in ('mailprobe',)
    for path in ('src/background.ts', 'manifest.json', 'background.html')
)
DECISION_PATH = 'docs/decisions/20261025-protocol-changelog.md'
CHANGELOG_ENTRY = '\n## Changelog\n\n### Fixed\n\n- Reject invalid connector frames.\n'


class ProtocolChangelogTests(GuardTestCase):
    def pull_request_for(self, paths):
        repo, environment = self.pull_request(
            {path: 'updated\n' for path in paths},
            {DECISION_PATH: '# Decision\n'},
        )
        environment['PR_DESCRIPTION'] = f'Decision: {DECISION_PATH}\n'
        return repo, environment

    def test_rust_protocol_change_requires_an_entry(self):
        for path in RUST_PROTOCOL_PATHS:
            with self.subTest(path=path):
                repo, environment = self.pull_request_for([path])
                result = self.run_guard(repo, 'raicho_check_pr.py', environment)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('no changelog entry', result.stderr)
                self.assertIn(path, result.stderr)

    def test_description_entry_satisfies_rust_protocol_changes(self):
        repo, environment = self.pull_request_for(RUST_PROTOCOL_PATHS)
        environment['PR_DESCRIPTION'] += CHANGELOG_ENTRY
        result = self.run_guard(repo, 'raicho_check_pr.py', environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('description has an entry', result.stdout)

    def test_probe_changes_need_no_entry_or_label(self):
        for path in PROBE_PATHS:
            with self.subTest(path=path):
                repo, environment = self.pull_request_for([path])
                result = self.run_guard(repo, 'raicho_check_pr.py', environment)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('no shipping change', result.stdout)

    def test_mixed_probe_and_production_changes_require_an_entry(self):
        for path in (
            'extension/src/background.ts',
            'protocol/rust/src/decode_frame.rs',
        ):
            with self.subTest(path=path):
                repo, environment = self.pull_request_for([*PROBE_PATHS, path])
                result = self.run_guard(repo, 'raicho_check_pr.py', environment)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('no changelog entry', result.stderr)
                self.assertIn(path, result.stderr)
                for probe_path in PROBE_PATHS:
                    self.assertNotIn(probe_path, result.stderr)

    def test_protocol_tests_and_generators_remain_nonshipping(self):
        paths = (
            'protocol/rust/tests/json_decoding.rs',
            'protocol/typescript/tests/contract.test.mjs',
            'protocol/generator/src/main.rs',
            'protocol/generator/raicho_protocol.py',
            'protocol/generator/tests/raicho_protocol_generation_tests.py',
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertFalse(is_shipping(path))
        repo, environment = self.pull_request_for(paths)
        result = self.run_guard(repo, 'raicho_check_pr.py', environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('no shipping change', result.stdout)
