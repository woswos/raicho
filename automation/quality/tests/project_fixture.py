import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from automation.paths import REPOSITORY_ROOT

MAKEFILE = REPOSITORY_ROOT / 'Makefile'


class ProjectFixture(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-tooling-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        subprocess.run(['git', 'init', '--quiet'], cwd=self.root, check=True)

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def check(self, target, successful=True, diagnostic=None):
        environment = {
            **os.environ,
            'CARGO_NET_OFFLINE': 'true',
            'CARGO_TARGET_DIR': str(self.root / 'target'),
        }
        result = subprocess.run(
            ['make', '-f', str(MAKEFILE), f'QUALITY_ROOT={self.root}', target],
            cwd=self.root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.verify(result, successful, diagnostic)

    def check_runner(self, target, successful=True, diagnostic=None, environment=None):
        result = subprocess.run(
            [sys.executable, '-B', '-m', 'automation.quality.runner', '--root', str(self.root), target],
            cwd=self.root,
            env={**os.environ, **(environment or {}), 'PYTHONPATH': str(REPOSITORY_ROOT)},
            capture_output=True,
            text=True,
            check=False,
        )
        self.verify(result, successful, diagnostic)

    def verify(self, result, successful, diagnostic):
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode == 0, successful, output)
        if diagnostic:
            self.assertIn(diagnostic, output)

    def git_only_environment(self):
        binaries = self.root / 'vendor'
        binaries.mkdir(exist_ok=True)
        (binaries / 'git').symlink_to(shutil.which('git'))
        return {**os.environ, 'PATH': str(binaries)}
