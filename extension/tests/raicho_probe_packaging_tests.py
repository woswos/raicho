import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BUILDER = 'extension.raicho_build_extension'
BUILD_ENVIRONMENT = os.environ | {'PYTHONPATH': str(REPOSITORY_ROOT)}


class ProbePackagingTests(unittest.TestCase):
    def test_probe_source_requires_explicit_selection(self):
        with tempfile.TemporaryDirectory() as temporary:
            outputs = Path(temporary)
            for label, arguments in (
                ('production', []),
                (
                    'probe',
                    ['--source-root', str(REPOSITORY_ROOT / 'extension/mailprobe')],
                ),
            ):
                archive_path = outputs / f'{label}.xpi'
                subprocess.run(
                    [
                        sys.executable,
                        '-B',
                        '-m',
                        BUILDER,
                        '--output',
                        str(archive_path),
                        *arguments,
                    ],
                    env=BUILD_ENVIRONMENT,
                    cwd=outputs,
                    check=True,
                )
                with zipfile.ZipFile(archive_path) as archive:
                    manifest = json.loads(archive.read('manifest.json'))
                    if label == 'production':
                        self.assertEqual(manifest['permissions'], ['storage'])
                        self.assertNotIn('dispatcher.js', archive.namelist())
                        self.assertIn(
                            'protocol/typescript/src/validator_generated.js',
                            archive.namelist(),
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
                                name.startswith('protocol/')
                                for name in archive.namelist()
                            )
                        )
