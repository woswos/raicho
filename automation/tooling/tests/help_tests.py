import re
import unittest

from automation.tooling.tests.deployment_tests import make


def make_list(name):
    return make('--eval', f'print-list: ; @echo $({name})', 'print-list').split()


class HelpTests(unittest.TestCase):
    def test_bare_make_prints_the_guide_on_the_host_and_in_the_container(self):
        for environment in ({}, {'RAICHO_TOOLING_CONTAINER': '1'}):
            with self.subTest(environment=environment):
                self.assertTrue(make(**environment).startswith('Raicho development\n'))

    def test_the_guide_names_every_target_outside_the_deployment_guide(self):
        guide = make('help')
        deployment = set(make_list('DEPLOYMENT_TARGETS')) - {'deploy'}
        for target in make_list('CONTAINER_TARGETS') + make_list('HOST_TARGETS'):
            if target not in deployment:
                with self.subTest(target=target):
                    self.assertRegex(guide, rf'(?<![\w-]){re.escape(target)}(?![\w-])')
        self.assertNotIn('\n# ', guide)

    def test_the_guide_uses_the_exported_colors(self):
        colored = make('help', TERM='xterm')
        for text in ('\x1b[36mCheck', '\x1b[32mmake lint', '\x1b[33mVERBOSE=1', '\x1b[33mTEST='):
            self.assertIn(text, colored)


if __name__ == '__main__':
    unittest.main()
