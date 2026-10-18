import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

BUILDER = Path(__file__).with_name('raicho_build_extension.py')


class ProbePackagingTests(unittest.TestCase):
    def test_probe_source_requires_explicit_selection(self):
        with tempfile.TemporaryDirectory() as temporary:
            outputs = Path(temporary)
            for label, arguments in (
                ('production', []),
                ('probe', ['--source-root', 'extension/mail_probe']),
            ):
                archive_path = outputs / f'{label}.xpi'
                subprocess.run(
                    [
                        sys.executable,
                        str(BUILDER),
                        '--output',
                        str(archive_path),
                        *arguments,
                    ],
                    check=True,
                )
                with zipfile.ZipFile(archive_path) as archive:
                    manifest = json.loads(archive.read('manifest.json'))
                    if label == 'production':
                        self.assertEqual(manifest['permissions'], ['storage'])
                        self.assertNotIn('dispatcher.js', archive.namelist())
                        self.assertIn(
                            'contract/validator_generated.js', archive.namelist()
                        )
                        self.assertNotIn('node_modules/', ''.join(archive.namelist()))
                    else:
                        self.assertNotIn('messages.send', manifest['permissions'])
                        self.assertEqual(
                            manifest['optional_permissions'], ['messages.send']
                        )
                        self.assertIn('dispatcher.js', archive.namelist())
                        self.assertIn('permission.html', archive.namelist())
                        self.assertFalse(
                            any(
                                name.startswith('contract/')
                                for name in archive.namelist()
                            )
                        )
