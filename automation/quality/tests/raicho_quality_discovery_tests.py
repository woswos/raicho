import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from automation.raicho_paths import REPOSITORY_ROOT

RUNNER = 'automation.quality.raicho_quality'


class QualityDiscoveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-discovery-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def check_failure(self, target, diagnostic, environment=None):
        result = subprocess.run(
            [sys.executable, '-B', '-m', RUNNER, '--root', str(self.root), target],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
            env={
                **os.environ,
                **(environment or {}),
                'PYTHONPATH': str(REPOSITORY_ROOT),
            },
        )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(diagnostic, result.stderr)

    def test_format_rejects_symlinks_into_excluded_content(self):
        vendor = self.root / 'vendor'
        vendor.mkdir()
        original = 'value=1\n'
        source = vendor / 'original.py'
        source.write_text(original)
        (self.root / 'linked.py').symlink_to(source)
        self.check_failure('format', 'not symlinks')
        self.assertEqual(source.read_text(), original)

    def test_broken_source_symlinks_cannot_look_like_absent_languages(self):
        (self.root / 'missing.rs').symlink_to(self.root / 'missing-target')
        self.check_failure('lint-rust', 'not symlinks')

    def test_unknown_targets_do_not_succeed(self):
        self.check_failure('lint-mistyped', 'invalid choice')

    def test_missing_tools_cannot_be_reported_as_not_applicable(self):
        binaries = self.root / 'vendor'
        binaries.mkdir()
        (binaries / 'git').symlink_to(shutil.which('git'))
        environment = {**os.environ, 'PATH': str(binaries)}
        self.check_failure('lint-rust', 'cargo is unavailable', environment)
