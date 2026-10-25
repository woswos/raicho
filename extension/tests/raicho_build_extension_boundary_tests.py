import posixpath
import re
import tempfile
import unittest
import zipfile
from pathlib import Path

from extension.tests.raicho_extension_build import run_builder
from extension.tests.raicho_inspect_connector_xpi import inspect_archive


class ExtensionBoundaryTests(unittest.TestCase):
    def test_production_excludes_probe_code_and_resolves_its_imports(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'production.xpi'
            result = run_builder('--output', str(output), cwd=directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            inspect_archive(output, b'unused-fixture-token')
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                self.assertIn('protocol/typescript/src/validator_generated.js', names)
                scripts = re.findall(
                    r'<script\b[^>]*\bsrc="([^"]+)"',
                    archive.read('background.html').decode(),
                )
                self.assertTrue(scripts)
                for script in scripts:
                    self.assertIn(script, names)
                for name in names:
                    self.assertNotIn('/tests/', name)
                    self.assertNotIn('mailprobe/', name)
                    self.assertNotIn('node_modules/', name)
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
