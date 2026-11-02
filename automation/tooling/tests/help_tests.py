import re
import tempfile
import unittest
from pathlib import Path

from automation.testing.docker_mock import DockerMock
from automation.tooling.tests.deployment_tests import make


def make_list(name):
    return make('--eval', f'print-list: ; @echo $({name})', 'print-list').split()


class HelpTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-help-test-')
        self.addCleanup(temporary.cleanup)
        self.state = Path(temporary.name)

    def test_bare_make_prints_the_guide_on_the_host_and_in_the_container(self):
        for environment in ({}, {'RAICHO_TOOLING_CONTAINER': '1'}):
            with self.subTest(environment=environment):
                self.assertTrue(make(**environment).startswith('Raicho development\n'))

    def test_the_guide_names_every_target_without_docker(self):
        docker = DockerMock(self.state / 'docker')
        guide = make('help', PATH=docker.environment()['PATH'])
        commands = set(re.findall(r'^  make ([a-z-]*[a-z])', guide, re.MULTILINE))
        for target in make_list('CONTAINER_TARGETS') + make_list('HOST_TARGETS'):
            with self.subTest(target=target):
                if target.startswith('deploy-connector-'):
                    self.assertIn(target.removeprefix('deploy-connector-'), guide)
                elif target not in commands:
                    # A family member such as lint-bash may appear in its parent's list.
                    self.assertTrue(any(target.startswith(f'{command}-') for command in commands))
                    self.assertRegex(guide, rf'(?<![\w-]){re.escape(target)}(?![\w-])')
        self.assertIn('make deploy-connector-<command>', guide)
        self.assertNotIn('make deploy ', guide)
        self.assertNotIn('\n# ', guide)
        self.assertEqual(docker.commands(), [])

    def test_the_host_guide_describes_the_selected_deployment(self):
        guide = make('help', COMPOSE_PROJECT_NAME='second', RAICHO_STATE_DIRECTORY=str(self.state), RAICHO_PORT='8081')
        for line in (
            'Current deployment',
            'project            second',
            f'state directory    {self.state}',
            'connector          not enrolled',
        ):
            self.assertIn(line, guide)
        self.assertIn('http://127.0.0.1:8081', guide)
        self.assertIn("project            it's", make('help', RAICHO_PROJECT="it's"))
        (self.state / 'credentials').mkdir()
        self.assertIn('connector          enrolled', make('help', RAICHO_STATE_DIRECTORY=str(self.state)))

    def test_the_container_guide_omits_the_deployment_settings(self):
        guide = make('help', RAICHO_TOOLING_CONTAINER='1')
        self.assertIn('make deploy-up', guide)
        self.assertNotIn('Current deployment', guide)

    def test_the_guide_uses_the_exported_colors(self):
        (self.state / 'credentials').mkdir()
        colored = make('help', TERM='xterm', RAICHO_STATE_DIRECTORY=str(self.state))
        for text in (
            '\x1b[36mCheck',
            '\x1b[32mmake lint',
            '\x1b[32mmake deploy-up',
            '\x1b[33mVERBOSE=1',
            '\x1b[33mTEST=',
            '\x1b[33mRAICHO_PROJECT',
            '\x1b[32menrolled',
        ):
            self.assertIn(text, colored)


if __name__ == '__main__':
    unittest.main()
