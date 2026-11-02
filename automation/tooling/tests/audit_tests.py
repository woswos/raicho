import subprocess
import unittest

from automation.paths import REPOSITORY_ROOT
from automation.tooling.tests.deployment_tests import dry_run

LOCKFILE_NAMES = ('Cargo.lock', 'package-lock.json', 'requirements.txt')


class AuditTests(unittest.TestCase):
    def test_the_audit_scans_every_tracked_lockfile(self):
        tracked = subprocess.run(
            ['git', 'ls-files'], cwd=REPOSITORY_ROOT, capture_output=True, text=True, check=True
        ).stdout.split()
        lockfiles = [path for path in tracked if path.rsplit('/', 1)[-1] in LOCKFILE_NAMES]
        commands = dry_run('audit', RAICHO_TOOLING_CONTAINER='1')
        self.assertTrue(lockfiles)
        for path in lockfiles:
            with self.subTest(path=path):
                self.assertIn(f' --lockfile {path}', commands)

    def test_quiet_audits_print_only_findings(self):
        self.assertIn(' --verbosity=error ', dry_run('audit', RAICHO_TOOLING_CONTAINER='1'))
        self.assertNotIn('--verbosity', dry_run('audit', RAICHO_TOOLING_CONTAINER='1', VERBOSE='1'))


if __name__ == '__main__':
    unittest.main()
