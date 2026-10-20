import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from policy import write_policies


class PolicyFixture:
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.runtime = self.root / 'runtime'
        self.extension = self.root / 'extension'
        self.extension.mkdir()
        self.manifest = self.extension / 'manifest.json'
        self.manifest.write_text(
            json.dumps(
                {
                    'version': '0.1.0',
                    'browser_specific_settings': {'gecko': {'id': 'connector@raicho'}},
                }
            )
        )
        (self.extension / 'raicho-0.1.0.xpi').touch()
        self.token_file = self.root / 'token'
        self.token = 'ab' * 32
        self.token_file.write_text(self.token + '\n')
        self.environment = {
            'RAICHO_CONNECTOR_ENDPOINT': 'ws://listener:8081/connector/v1',
            'RAICHO_CONNECTOR_TOKEN_FILE': str(self.token_file),
        }


class PolicyTests(PolicyFixture, unittest.TestCase):
    def test_unconfigured_install_preserves_application_update_policy(self):
        destination = write_policies(self.runtime, self.extension, {})
        policies = json.loads(destination.read_text())['policies']
        self.assertTrue(policies['DisableAppUpdate'])
        self.assertNotIn('3rdparty', policies)
        self.assertEqual(
            policies['ExtensionSettings']['connector@raicho'],
            {
                'installation_mode': 'force_installed',
                'install_url': (self.extension / 'raicho-0.1.0.xpi').as_uri(),
                'updates_disabled': True,
            },
        )

    def test_managed_configuration_and_private_permissions(self):
        self.runtime.mkdir(mode=0o755)
        destination = write_policies(self.runtime, self.extension, self.environment)
        settings = json.loads(destination.read_text())['policies']['3rdparty']
        self.assertEqual(
            settings['Extensions']['connector@raicho'],
            {
                'endpoint': self.environment['RAICHO_CONNECTOR_ENDPOINT'],
                'token': self.token,
            },
        )
        self.assertEqual(destination.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.runtime.stat().st_mode & 0o777, 0o700)
        self.assertEqual(destination.name, 'policies.json')

    def test_repeated_startup_replaces_complete_policy_without_stale_credentials(self):
        destination = write_policies(self.runtime, self.extension, self.environment)
        original_inode = destination.stat().st_ino
        write_policies(self.runtime, self.extension, {})
        self.assertNotEqual(destination.stat().st_ino, original_inode)
        self.assertNotIn(self.token, destination.read_text())
        self.assertNotIn('3rdparty', json.loads(destination.read_text())['policies'])
        self.assertEqual(list(self.runtime.iterdir()), [destination])

    def test_failed_atomic_replace_preserves_existing_policy_and_removes_temporary(
        self,
    ):
        destination = write_policies(self.runtime, self.extension, {})
        original = destination.read_bytes()
        with patch(
            'policy.os.replace', side_effect=OSError('mock replacement failure')
        ):
            with self.assertRaises(OSError):
                write_policies(self.runtime, self.extension, self.environment)
        self.assertEqual(destination.read_bytes(), original)
        self.assertEqual(list(self.runtime.iterdir()), [destination])

    def test_atomic_replace_uses_fully_written_private_file(self):
        original_replace = os.replace

        def inspect_replace(source, destination):
            source_path = Path(source)
            self.assertEqual(source_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(
                json.loads(source_path.read_text())['policies']['DisableAppUpdate'],
                True,
            )
            self.assertEqual(source_path.parent, self.runtime)
            original_replace(source, destination)

        with patch('policy.os.replace', side_effect=inspect_replace):
            write_policies(self.runtime, self.extension, self.environment)

    def test_runtime_symlink_is_rejected(self):
        self.runtime.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Runtime directory'):
            write_policies(self.runtime, self.extension, {})
        self.assertFalse((self.root / 'policies.json').exists())

    def test_packaged_version_selects_upgrade_archive(self):
        write_policies(self.runtime, self.extension, {})
        manifest = json.loads(self.manifest.read_text())
        manifest['version'] = '0.1.1'
        self.manifest.write_text(json.dumps(manifest))
        archive = self.extension / 'raicho-0.1.1.xpi'
        archive.touch()
        destination = write_policies(self.runtime, self.extension, {})
        extension = json.loads(destination.read_text())['policies']['ExtensionSettings']
        self.assertEqual(extension['connector@raicho']['install_url'], archive.as_uri())


if __name__ == '__main__':
    unittest.main()
