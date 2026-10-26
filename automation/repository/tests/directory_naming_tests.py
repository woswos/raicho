import tempfile
from pathlib import Path

from automation.testing.guard_fixtures import GuardTestCase, module_name

SCRIPT = 'check_directory_naming.py'
INVALID_NAMES = (
    'Uppercase',
    'mail_probe',
    'mail-probe',
    'mail probe',
    'mail.probe',
    '雷鳥',
)


class DirectoryNamingTests(GuardTestCase):
    def check(self, repo):
        return self.run_guard(repo, SCRIPT, {})

    def test_accepts_lowercase_letters_digits_and_reserved_tool_paths(self):
        repo = self.repo()
        for name in (
            'mailprobe/tests',
            'docs/contributing',
            'assets/brand',
            'versions/123',
            '.agents/skills/write-plan-doc',
            '.github/workflows',
            '.github/PULL_REQUEST_TEMPLATE',
        ):
            repo.write(f'{name}/File-Name.md', '')
        result = self.check(repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('directory-naming check passed', result.stdout)

    def test_skill_directories_use_kebab_case(self):
        repo = self.repo()
        for name in (
            '.agents/skills/write-plan-doc',
            '.agents/skills/Bad_Skill',
            'docs/write-plan-doc',
        ):
            repo.write(f'{name}/SKILL.md', '')
        result = self.check(repo)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr.count('FAIL:'), 2)
        self.assertIn(
            'FAIL: .agents/skills/Bad_Skill must use lowercase kebab-case',
            result.stderr,
        )
        self.assertIn(
            'FAIL: docs/write-plan-doc must use lowercase letters and digits only',
            result.stderr,
        )

    def test_rejects_uppercase_separators_spaces_dots_and_non_ascii(self):
        repo = self.repo()
        for name in INVALID_NAMES:
            repo.write(f'source/{name}/file.txt', '')
        result = self.check(repo)
        self.assertEqual(result.returncode, 1)
        for name in INVALID_NAMES:
            self.assertIn(f'FAIL: source/{name}', result.stderr)

    def test_checks_each_nested_directory_once(self):
        repo = self.repo()
        repo.write('Bad/also_bad/first.txt', '')
        repo.write('Bad/also_bad/second.txt', '')
        result = self.check(repo)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr.count('FAIL:'), 2)
        self.assertIn('FAIL: Bad must', result.stderr)
        self.assertIn('FAIL: Bad/also_bad must', result.stderr)

    def test_reserved_names_are_allowed_only_at_their_exact_paths(self):
        repo = self.repo()
        for name in (
            'docs/.agents',
            'docs/.github',
            'docs/PULL_REQUEST_TEMPLATE',
            '.github/pull_request_template',
            '.github/PULL_REQUEST_TEMPLATE_extra',
            '.github/PULL_REQUEST_TEMPLATE/Bad',
        ):
            repo.write(f'{name}/file.md', '')
        result = self.check(repo)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr.count('FAIL:'), 6)

    def test_checks_tracked_and_untracked_paths_but_not_ignored_paths(self):
        repo = self.repo()
        repo.write('tracked_bad/file.txt', '')
        repo.commit()
        repo.write('.gitignore', '*ignored*/\n')
        repo.write('untracked_bad/file.txt', '')
        repo.write('ignored_bad/file.txt', '')
        result = self.check(repo)
        self.assertEqual(result.returncode, 1)
        self.assertIn('tracked_bad', result.stderr)
        self.assertIn('untracked_bad', result.stderr)
        self.assertNotIn('ignored_bad', result.stderr)

    def test_tracked_ignored_and_missing_paths_still_have_names_checked(self):
        repo = self.repo()
        repo.write('tracked_bad/file.txt', '')
        repo.write('missing_bad/file.txt', '')
        repo.commit()
        repo.write('.gitignore', 'tracked_bad/\n')
        (repo.root / 'missing_bad/file.txt').unlink()
        (repo.root / 'missing_bad').rmdir()
        result = self.check(repo)
        self.assertEqual(result.returncode, 1)
        self.assertIn('tracked_bad', result.stderr)
        self.assertIn('missing_bad', result.stderr)

    def test_excludes_dependencies_outputs_and_historical_references(self):
        repo = self.repo()
        for name in (
            'node_modules',
            'target',
            'dist',
            'vendor',
            '__pycache__',
            'nested/node_modules',
            'nested/.git',
            'assets/brand/references',
        ):
            repo.write(f'{name}/Bad_Name/file.txt', '')
        repo.commit()
        result = self.check(repo)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_exclusion_does_not_hide_an_invalid_owned_parent(self):
        repo = self.repo()
        repo.write('Bad/node_modules/package/file.txt', '')
        result = self.check(repo)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr.count('FAIL:'), 1)
        self.assertIn('FAIL: Bad must', result.stderr)

    def test_rejects_non_git_roots_clearly(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_command(
                ['python3', '-B', '-m', module_name(SCRIPT), directory],
                Path(directory),
                {},
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn('cannot inspect Git repository', result.stderr)

    def test_rejects_a_subdirectory_instead_of_the_repository_root(self):
        repo = self.repo()
        repo.write('nested/file.txt', '')
        result = self.run_command(
            ['python3', '-B', '-m', module_name(SCRIPT), str(repo.root / 'nested')],
            repo.root,
            {},
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn('expected Git repository root', result.stderr)
