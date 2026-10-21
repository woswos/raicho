import json
import posixpath
import re
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
                names = set(archive.namelist())
                self.assertIn('extension/src/connector_transport.js', names)
                self.assertNotIn('lifecycle_probe.js', names)
                scripts = re.findall(
                    r'<script\b[^>]*\bsrc="([^"]+)"',
                    archive.read('background.html').decode(),
                )
                self.assertTrue(scripts)
                for script in scripts:
                    self.assertIn(script, names)
                for name in names:
                    self.assertNotIn(b'lifecycle_probe', archive.read(name))
                    self.assertNotIn(b'mail_probe', archive.read(name))
                    self.assertNotIn('/tests/', name)
                    if name.endswith('.js'):
                        imports = re.findall(
                            r'\b(?:from|import)\s*["\']([^"\']+)["\']',
                            archive.read(name).decode(),
                        )
                        for module in imports:
                            self.assertTrue(module.startswith('.'), module)
                            target = posixpath.normpath(
                                posixpath.join(posixpath.dirname(name), module)
                            )
                            self.assertIn(target, names, f'{name} imports {module}')

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
