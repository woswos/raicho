import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

BUILDER = Path(__file__).with_name('raicho_build_extension.py')


class ExtensionPackagingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-extension-test-')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)

    def build(self, name, *arguments):
        output = self.directory / name
        subprocess.run(
            [sys.executable, str(BUILDER), '--output', str(output), *arguments],
            check=True,
            env=os.environ,
        )
        return output

    def test_reproducible_archive_has_only_runtime_files(self):
        first = self.build('first.xpi')
        second = self.build('second.xpi')
        self.assertEqual(first.read_bytes(), second.read_bytes())
        with zipfile.ZipFile(first) as archive:
            names = archive.namelist()
            self.assertEqual(names, sorted(names))
            self.assertIn('background.html', names)
            self.assertIn('extension/src/background.js', names)
            self.assertTrue(
                all(name.endswith(('.js', '.html', '.json')) for name in names)
            )
            self.assertNotIn('package.json', names)
            manifest = json.loads(archive.read('manifest.json'))
            self.assertEqual(manifest['permissions'], ['storage'])
            self.assertTrue(manifest['background']['persistent'])
            self.assertEqual(manifest['manifest_version'], 2)
            for entry in archive.infolist():
                self.assertEqual(entry.date_time, (1980, 1, 1, 0, 0, 0))

    def test_upgrade_changes_version_without_changing_identity(self):
        output = self.build('upgrade.xpi', '--version', '0.1.1')
        with zipfile.ZipFile(output) as archive:
            manifest = json.loads(archive.read('manifest.json'))
        self.assertEqual(manifest['version'], '0.1.1')
        self.assertEqual(
            manifest['browser_specific_settings']['gecko']['id'], 'connector@raicho'
        )

    def test_rejects_unsafe_output_and_version(self):
        for arguments in (
            ['--output', 'relative.xpi'],
            ['--output', str(self.directory / 'bad.xpi'), '--version', '../bad'],
            ['--output', str(self.directory / 'bad.xpi'), '--version', '65536.0.0'],
            ['--output', str(self.directory / 'bad.xpi'), '--version', '01.2.3'],
            ['--output', str(self.directory / 'bad.xpi'), '--version', ''],
        ):
            result = subprocess.run(
                [sys.executable, str(BUILDER), *arguments],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('FAIL:', result.stderr)

    def fixture_builder(self, version):
        source_root = self.directory / 'source'
        extension_root = source_root / 'extension'
        shutil.copytree(BUILDER.parent.parent / 'extension', extension_root)
        shutil.copytree(
            BUILDER.parent.parent / 'protocol/typescript',
            source_root / 'protocol/typescript',
        )
        builder = source_root / 'devbin' / BUILDER.name
        builder.parent.mkdir()
        shutil.copyfile(BUILDER, builder)
        manifest_path = extension_root / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['version'] = version
        manifest_path.write_text(json.dumps(manifest))
        return builder

    def test_image_artifacts_follow_manifest_version_and_explicit_override(self):
        builder = self.fixture_builder('0.2.3')
        for version, arguments in (('0.2.3', []), ('0.3.0', ['--version', '0.3.0'])):
            output = self.directory / version
            subprocess.run(
                [
                    sys.executable,
                    str(builder),
                    '--output-directory',
                    str(output),
                    *arguments,
                ],
                check=True,
            )
            self.assertEqual(
                sorted(path.name for path in output.iterdir()),
                ['manifest.json', f'raicho-{version}.xpi'],
            )
            metadata = json.loads((output / 'manifest.json').read_text())
            self.assertEqual(metadata['version'], version)
            with zipfile.ZipFile(output / f'raicho-{version}.xpi') as archive:
                self.assertEqual(json.loads(archive.read('manifest.json')), metadata)

    def test_rejects_invalid_default_manifest_version(self):
        builder = self.fixture_builder('65536.0.0')
        result = subprocess.run(
            [
                sys.executable,
                str(builder),
                '--output-directory',
                str(self.directory / 'artifacts'),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('FAIL:', result.stderr)
        self.assertFalse((self.directory / 'artifacts').exists())

    def test_output_modes_are_mutually_exclusive(self):
        result = subprocess.run(
            [
                sys.executable,
                str(BUILDER),
                '--output',
                str(self.directory / 'out.xpi'),
                '--output-directory',
                str(self.directory / 'artifacts'),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('not allowed with argument', result.stderr)
