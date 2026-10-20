import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TOOLING_IMAGE = '${RAICHO_TEST_TOOLING_IMAGE:?Set the disposable tooling image}'


def services(filename):
    return yaml.safe_load((ROOT / 'compose' / filename).read_text())['services']


class TestImageTests(unittest.TestCase):
    def test_mock_services_share_the_tooling_image_and_remain_isolated(self):
        configurations = {
            'compose.extension_test.yaml': ('probe', 'check'),
            'compose.mail_test.yaml': ('probe', 'mail-proxy', 'driver', 'extension'),
        }
        for filename, names in configurations.items():
            configured = services(filename)
            for name in names:
                with self.subTest(file=filename, service=name):
                    service = configured[name]
                    self.assertEqual(service['image'], TOOLING_IMAGE)
                    self.assertEqual(service['user'], '10001:10001')
                    self.assertTrue(service['read_only'])
                    self.assertEqual(service['cap_drop'], ['ALL'])
                    self.assertEqual(
                        service['security_opt'], ['no-new-privileges:true']
                    )
                    self.assertNotIn('ports', service)
                    self.assertNotIn('cap_add', service)
                    if name == 'extension':
                        self.assertEqual(service['network_mode'], 'none')
                    else:
                        self.assertNotIn('../extension/', str(service['volumes']))

    def test_mail_fixture_mounts_only_the_disposable_test_artifact(self):
        configured = services('compose.mail_test.yaml')
        thunderbird = configured['thunderbird']
        self.assertNotEqual(thunderbird['image'], TOOLING_IMAGE)
        extension = next(
            mount
            for mount in thunderbird['volumes']
            if isinstance(mount, dict)
            and mount.get('target') == '/opt/raicho/extension'
        )
        self.assertTrue(extension['read_only'])
        self.assertTrue(extension['volume']['nocopy'])
        artifact = extension['source']
        self.assertIn(f'{artifact}:/artifact', configured['extension']['volumes'])
        self.assertIn(
            '../extension/mail_probe/tests/profile:/mail_profile:ro',
            thunderbird['volumes'],
        )
        self.assertEqual(
            thunderbird['entrypoint'],
            ['/usr/bin/tini', '--', 'python3', '-B', '/mail_profile/start.py'],
        )
        self.assertEqual(
            thunderbird['environment']['LD_LIBRARY_PATH'], '/opt/thunderbird'
        )


if __name__ == '__main__':
    unittest.main()
