import unittest

from automation.testing.docker_mock import Response
from automation.tooling.tests.cleanup_fixture import PROJECT_FILTER, CleanupFixture


def listing(kind, project, output):
    return Response((kind, '--quiet', f'{PROJECT_FILTER}{project}'), output=output)


class MrproperTests(CleanupFixture):
    def mrproper(self, *responses, **options):
        return self.run_script('mrproper.bash', *responses, **options)

    def test_stops_every_deployment_and_tooling_container_but_keeps_their_data(self):
        tokens = [
            self.write('.raicho/raicho/credentials/connector.token', 'secret\n'),
            self.write('.raicho/staging/credentials/connector.token', 'secret\n'),
        ]
        self.write('.raicho/Invalid Name/notes.txt')
        commands, result = self.mrproper(
            listing('container', 'raicho', 'deployment\n'),
            listing('network', 'raicho', 'deployment-network\n'),
            listing('container', 'staging', 'staging\n'),
            listing('container', 'raicho-tools', 'tooling\n'),
        )
        for container in ('deployment', 'staging', 'tooling'):
            with self.subTest(container=container):
                self.assertIn(['container', 'stop', container], commands)
                self.assertIn(['container', 'rm', container], commands)
        self.assertIn(['network', 'rm', 'deployment-network'], commands)
        volumes = [command for command in commands if command[:2] == ['volume', 'rm']]
        self.assertEqual(volumes, [['volume', 'rm', 'raicho-tools_cache']])
        self.assertLess(
            commands.index(['container', 'stop', 'tooling']), commands.index(['volume', 'rm', 'raicho-tools_cache'])
        )
        projects = {
            word.removeprefix(PROJECT_FILTER)
            for command in commands
            if command[:2] == ['container', 'ls']
            for word in command
            if word.startswith(PROJECT_FILTER)
        }
        self.assertEqual(projects, {'raicho', 'staging', 'raicho-tools'})
        for token in tokens:
            with self.subTest(token=token):
                self.assertTrue(token.exists())
        self.assertIn('Removed the containers of staging', result.stdout)

    def test_a_failed_docker_listing_stops_before_removing_images(self):
        commands, result = self.mrproper(
            Response(('container', '--quiet', f'{PROJECT_FILTER}raicho'), status=1), status=1
        )
        self.assertNotIn('image', {command[0] for command in commands})
        self.assertNotIn('Mrproper finished', result.stdout)

    def test_removes_project_images_after_cleaning(self):
        commands, result = self.mrproper(Response(('image', 'rm', 'raicho-server:local'), status=1))
        self.assertIn('Removed image raicho-tools:local', result.stdout)
        self.assertIn('Kept image raicho-server:local', result.stderr)
        self.assertLess(
            commands.index(['volume', 'rm', 'raicho-tools_cache']),
            commands.index(['image', 'rm', 'raicho-tools:local']),
        )


if __name__ == '__main__':
    unittest.main()
