import unittest

import yaml

from automation.paths import REPOSITORY_ROOT

TOOLING_IMAGE = '${RAICHO_TEST_TOOLING_IMAGE:?Set the disposable tooling image}'


def services(filename):
    return yaml.safe_load((REPOSITORY_ROOT / filename).read_text())['services']


class TestImageTests(unittest.TestCase):
    def test_mock_services_share_the_tooling_image_and_remain_isolated(self):
        configurations = {
            'mailprobe/compose.yaml': (
                'probe',
                'mail-proxy',
                'driver',
                'extension',
            ),
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
                        self.assertEqual(service['volumes'], ['fixture:/config'])

    def test_mail_fixture_mounts_only_the_disposable_test_artifact(self):
        configured = services('mailprobe/compose.yaml')
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
            './tests/profile:/mail_profile:ro',
            thunderbird['volumes'],
        )
        self.assertEqual(
            thunderbird['entrypoint'],
            ['/usr/bin/tini', '--', 'python3', '-B', '/mail_profile/profile_start.py'],
        )
        self.assertEqual(
            thunderbird['environment']['LD_LIBRARY_PATH'], '/opt/thunderbird'
        )


if __name__ == '__main__':
    unittest.main()
