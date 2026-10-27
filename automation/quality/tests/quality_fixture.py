import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from automation.paths import REPOSITORY_ROOT

MAKEFILE = REPOSITORY_ROOT / 'Makefile'


class QualityFixture(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-tooling-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

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
        output = result.stdout + result.stderr
        if successful:
            self.assertEqual(result.returncode, 0, output)
        else:
            self.assertNotEqual(result.returncode, 0, output)
        if diagnostic:
            self.assertIn(diagnostic, output)
