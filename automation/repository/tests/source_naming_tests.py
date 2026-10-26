import tempfile
from pathlib import Path

from automation.testing.guard_fixtures import GuardTestCase, module_name

SCRIPT = 'check_source_naming.py'
EXTENSIONS = (
    'rs',
    'py',
    'pyi',
    'bash',
    'sh',
    'js',
    'mjs',
    'cjs',
    'jsx',
    'ts',
    'tsx',
    'mts',
    'cts',
    'sql',
    'html',
    'css',
)


class SourceNamingTests(GuardTestCase):
    def check(self, repo):
        return self.run_guard(repo, SCRIPT, {})

    def test_all_languages_accept_snake_case_and_numeric_prefixes(self):
        repo = self.repo()
        for extension in EXTENSIONS:
            repo.write(f'source-directory/valid_name.{extension}', '')
        repo.write('server/migrations/0000_create_state.sql', '')
        repo.write('source/1234_valid_name.sql', '')
        result = self.check(repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('source-naming check passed', result.stdout)

    def test_all_languages_reject_hyphens(self):
        repo = self.repo()
        for extension in EXTENSIONS:
            repo.write(f'source/bad-name.{extension}', '')
        result = self.check(repo)
        self.assertEqual(result.returncode, 1)
        for extension in EXTENSIONS:
            self.assertIn(f'FAIL: source/bad-name.{extension}', result.stderr)
        self.assertIn('snake_case', result.stderr)

    def test_rejects_case_spaces_and_unrecognized_dotted_suffixes(self):
        repo = self.repo()
        names = [
            'BadName.py',
            'bad name.js',
            'name.TS',
            'bad.extra.rs',
            'bad__name.sql',
        ]
        for name in names:
            repo.write(name, '')
        result = self.check(repo)
        self.assertEqual(result.returncode, 1)
        for name in names:
            self.assertIn(f'FAIL: {name}', result.stderr)

    def test_preserves_conventional_suffixes_and_python_special_names(self):
        repo = self.repo()
        names = [
            'polling.test.mjs',
            'polling.spec.ts',
            'globals.d.ts',
            'globals.d.mts',
            'globals.d.cts',
            'status.module.css',
            'eslint.config.mjs',
            'vite.config.ts',
            '__init__.py',
            '__main__.py',
            '__init__.pyi',
            '.eslintrc.cjs',
            '.prettierrc.js',
        ]
        for name in names:
            repo.write(name, '')
        self.assertEqual(self.check(repo).returncode, 0)

    def test_conventional_suffixes_do_not_bypass_stem_or_language_rules(self):
        repo = self.repo()
        names = ['bad-name.test.mjs', 'bad-name.d.ts', 'bad.test.sql', 'Bad.config.ts']
        for name in names:
            repo.write(name, '')
        result = self.check(repo)
        self.assertEqual(result.returncode, 1)
        for name in names:
            self.assertIn(f'FAIL: {name}', result.stderr)

    def test_checks_tracked_and_untracked_files_but_not_ignored_files(self):
        repo = self.repo()
        repo.write('tracked-bad.py', '')
        repo.commit()
        repo.write('.gitignore', '*ignored*\n')
        repo.write('untracked-bad.ts', '')
        repo.write('ignored-bad.rs', '')
        result = self.check(repo)
        self.assertIn('tracked-bad.py', result.stderr)
        self.assertIn('untracked-bad.ts', result.stderr)
        self.assertNotIn('ignored-bad.rs', result.stderr)

    def test_tracked_ignored_and_missing_paths_still_have_names_checked(self):
        repo = self.repo()
        repo.write('tracked-bad.py', '')
        repo.write('missing-bad.rs', '')
        repo.commit()
        repo.write('.gitignore', '*.py\n')
        (repo.root / 'missing-bad.rs').unlink()
        result = self.check(repo)
        self.assertIn('tracked-bad.py', result.stderr)
        self.assertIn('missing-bad.rs', result.stderr)

    def test_excludes_dependencies_outputs_history_and_non_source_files(self):
        repo = self.repo()
        directories = [
            'node_modules',
            'target',
            'dist',
            'vendor',
            '__pycache__',
            'assets/brand/references',
            'nested/node_modules',
        ]
        for directory in directories:
            repo.write(f'{directory}/Bad-Name.js', '')
        for name in ['docs/old-style.md', 'assets/brand/logo-dark.svg', 'Cargo.toml']:
            repo.write(name, '')
        repo.commit()
        self.assertEqual(self.check(repo).returncode, 0)

    def test_checks_extensionless_shell_sources_only(self):
        repo = self.repo()
        repo.write('valid_script', '#!/usr/bin/env bash\n')
        headers = {
            'bad-script': '#!/bin/sh',
            'bash-arguments': '#!/bin/bash -e',
            'usr-bash': '#!/usr/bin/bash',
            'env-split': '#!/usr/bin/env -S bash -e',
        }
        for name, header in headers.items():
            repo.write(name, header + '\n')
        repo.write('ordinary-file', 'data\n#!/bin/bash\n')
        repo.write('python-file', '#!/usr/bin/env python3\n')
        result = self.check(repo)
        for name in headers:
            self.assertIn(f'FAIL: {name}', result.stderr)
        self.assertNotIn('valid_script', result.stderr)
        self.assertNotIn('ordinary-file', result.stderr)
        self.assertNotIn('python-file', result.stderr)

    def test_invalid_root_fails_clearly(self):
        with tempfile.TemporaryDirectory() as directory:
            command = ['python3', '-B', '-m', module_name(SCRIPT), directory]
            result = self.run_command(command, Path(directory), {})
        self.assertEqual(result.returncode, 1)
        self.assertIn('FAIL:', result.stderr)
        self.assertIn('Git repository', result.stderr)
