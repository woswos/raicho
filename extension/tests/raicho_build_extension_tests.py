import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from automation.raicho_paths import REPOSITORY_ROOT
from extension.tests.raicho_extension_build import run_builder


class ExtensionPackagingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-extension-test-')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)

    def build(self, name, *arguments):
        output = self.directory / name
        result = run_builder('--output', str(output), *arguments, cwd=self.directory)
        self.assertEqual(result.returncode, 0, result.stderr)
        return output

    def assert_rejected(self, result, message='FAIL:'):
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(message, result.stderr)

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
            self.assertFalse(
                any(
                    name.startswith(('automation/', 'runtime/', 'protocol/generator/'))
                    for name in names
                )
            )
            manifest = json.loads(archive.read('manifest.json'))
            self.assertTrue(manifest['background']['persistent'])
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
        bad = str(self.directory / 'bad.xpi')
        for arguments in (
            ['--output', 'relative.xpi'],
            ['--output', bad, '--version', '../bad'],
            ['--output', bad, '--version', '65536.0.0'],
            ['--output', bad, '--version', '01.2.3'],
            ['--output', bad, '--version', ''],
        ):
            with self.subTest(arguments=arguments):
                self.assert_rejected(run_builder(*arguments))

    def source_with_version(self, version):
        source_root = self.directory / 'source'
        extension_root = source_root / 'extension'
        shutil.copytree(REPOSITORY_ROOT / 'extension', extension_root)
        shutil.copytree(
            REPOSITORY_ROOT / 'protocol/typescript',
            source_root / 'protocol/typescript',
        )
        manifest_path = extension_root / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['version'] = version
        manifest_path.write_text(json.dumps(manifest))
        return source_root

    def test_image_artifacts_follow_manifest_version_and_explicit_override(self):
        source_root = self.source_with_version('0.2.3')
        for version, arguments in (('0.2.3', []), ('0.3.0', ['--version', '0.3.0'])):
            output = self.directory / version
            result = run_builder(
                '--output-directory',
                str(output),
                *arguments,
                source_root=source_root,
                cwd=self.directory,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                sorted(path.name for path in output.iterdir()),
                ['manifest.json', f'raicho-{version}.xpi'],
            )
            metadata = json.loads((output / 'manifest.json').read_text())
            self.assertEqual(metadata['version'], version)
            with zipfile.ZipFile(output / f'raicho-{version}.xpi') as archive:
                self.assertEqual(json.loads(archive.read('manifest.json')), metadata)

    def test_rejects_invalid_default_manifest_version(self):
        source_root = self.source_with_version('65536.0.0')
        artifacts = self.directory / 'artifacts'
        self.assert_rejected(
            run_builder(
                '--output-directory',
                str(artifacts),
                source_root=source_root,
                cwd=self.directory,
            )
        )
        self.assertFalse(artifacts.exists())

    def test_output_modes_are_mutually_exclusive(self):
        self.assert_rejected(
            run_builder(
                '--output',
                str(self.directory / 'out.xpi'),
                '--output-directory',
                str(self.directory / 'artifacts'),
            ),
            'exactly one extension output mode',
        )
