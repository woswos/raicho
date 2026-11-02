import unittest

from automation.tooling.tests.deployment_tests import dry_run, make


class ContainerMakeTests(unittest.TestCase):
    def test_only_the_filtered_suites_receive_the_test_filter(self):
        probe = 'probe: ; @printenv TEST || echo unset'
        self.assertEqual(make('--eval', probe, 'probe', RAICHO_TOOLING_CONTAINER='1', TEST='name'), 'unset\n')
        for target in ('test-python', 'test-server'):
            with self.subTest(target=target):
                self.assertIn("TEST='name' ", dry_run(target, RAICHO_TOOLING_CONTAINER='1', TEST='name'))
        self.assertNotIn('TEST=', dry_run('test-web', RAICHO_TOOLING_CONTAINER='1', TEST='name'))


if __name__ == '__main__':
    unittest.main()
