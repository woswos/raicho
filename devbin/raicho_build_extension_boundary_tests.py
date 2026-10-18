import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

BUILDER = Path(__file__).with_name('raicho_build_extension.py')


class ExtensionBoundaryTests(unittest.TestCase):
    def test_production_excludes_probe_code(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'production.xpi'
            subprocess.run(
                [sys.executable, str(BUILDER), '--output', str(output)], check=True
            )
            with zipfile.ZipFile(output) as archive:
                self.assertIn('connector_transport.js', archive.namelist())
                self.assertNotIn('lifecycle_probe.js', archive.namelist())
                for name in archive.namelist():
                    self.assertNotIn(b'lifecycle_probe', archive.read(name))
                    self.assertNotIn(b'mail_probe', archive.read(name))

    def test_lifecycle_probe_is_an_explicit_separate_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'lifecycle.xpi'
            subprocess.run(
                [
                    sys.executable,
                    str(BUILDER),
                    '--output',
                    str(output),
                    '--source-root',
                    str(BUILDER.parent.parent / 'extension' / 'lifecycle_probe'),
                ],
                check=True,
            )
            with zipfile.ZipFile(output) as archive:
                self.assertIn('lifecycle_probe.js', archive.namelist())
                self.assertNotIn('connector_transport.js', archive.namelist())
                manifest = json.loads(archive.read('manifest.json'))
                self.assertEqual(manifest['permissions'], ['storage'])
