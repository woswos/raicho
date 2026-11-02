import fnmatch
import subprocess
import unittest

from automation.paths import REPOSITORY_ROOT
from automation.tooling.tests.deployment_tests import dry_run

LOCKFILE_PATTERNS = (
    '*.lock',
    '*-lock.json',
    '*.lock.json',
    '*-lock.yaml',
    '*.lockfile',
    'requirements*.txt',
    'pylock*.toml',
    'go.sum',
)


def is_lockfile(path):
    return any(fnmatch.fnmatch(path.rsplit('/', 1)[-1], pattern) for pattern in LOCKFILE_PATTERNS)


class AuditTests(unittest.TestCase):
    def test_the_audit_scans_every_tracked_lockfile(self):
        tracked = subprocess.run(
            ['git', 'ls-files'], cwd=REPOSITORY_ROOT, capture_output=True, text=True, check=True
        ).stdout.split()
        lockfiles = [path for path in tracked if is_lockfile(path)]
        commands = dry_run('audit', RAICHO_TOOLING_CONTAINER='1')
        self.assertTrue(lockfiles)
        for path in lockfiles:
            with self.subTest(path=path):
                self.assertIn(f' --lockfile {REPOSITORY_ROOT}/{path}', commands)

    def test_the_patterns_cover_the_scanner_lockfile_formats(self):
        names = (
            'Cargo.lock',
            'uv.lock',
            'package-lock.json',
            'packages.lock.json',
            'pnpm-lock.yaml',
            'gradle.lockfile',
            'requirements-dev.txt',
            'pylock.toml',
            'pylock.dev.toml',
            'go.sum',
        )
        for name in names:
            with self.subTest(name=name):
                self.assertTrue(is_lockfile(f'nested/{name}'))

    def test_quiet_audits_print_only_findings(self):
        self.assertIn(' --verbosity=error ', dry_run('audit', RAICHO_TOOLING_CONTAINER='1'))
        self.assertNotIn('--verbosity', dry_run('audit', RAICHO_TOOLING_CONTAINER='1', VERBOSE='1'))


if __name__ == '__main__':
    unittest.main()
