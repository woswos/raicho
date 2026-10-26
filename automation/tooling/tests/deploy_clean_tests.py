import unittest

from automation.testing.docker_mock import Response
from automation.tooling.tests.cleanup_fixture import PROJECT_FILTER, CleanupFixture

NAMES = '{{.Name}}'


def deployment(project='raicho'):
    return (
        Response(
            ('container', '--format', '{{.Names}}', f'{PROJECT_FILTER}{project}'), output=f'{project}-thunderbird-1\n'
        ),
        Response(('volume', '--format', NAMES, f'{PROJECT_FILTER}{project}'), output=f'{project}_thunderbird-data\n'),
    )


def down(commands):
    return [command for command in commands if command[:1] == ['compose']]


class DeployCleanTests(CleanupFixture):
    def deploy_clean(self, *responses, **options):
        return self.run_script('deploy_clean.bash', *responses, **options)

    def test_a_wrong_or_missing_answer_removes_nothing(self):
        token = self.write('.raicho/raicho/credentials/connector.token', 'secret\n')
        for answer in ('', 'yes\n', 'raicho-second\n'):
            with self.subTest(answer=answer):
                commands, result = self.deploy_clean(*deployment(), answer=answer, status=1)
                self.assertEqual(down(commands), [])
                self.assertTrue(token.exists())
                self.assertIn('Cancelled. Nothing was removed.', result.stderr)
                self.assertIn('volume raicho_thunderbird-data', result.stdout)

    def test_the_project_name_confirms_the_removal(self):
        state = self.root / '.raicho/raicho'
        self.write('.raicho/raicho/credentials/connector.token', 'secret\n')
        self.write('.raicho/raicho/operation.lock')
        commands, result = self.deploy_clean(
            *deployment(),
            Response(('volume', '--quiet', f'{PROJECT_FILTER}raicho'), output='leftover\n'),
            answer='raicho\n',
        )
        self.assertEqual(
            down(commands),
            [['compose', '-p', 'raicho', '-f', f'{self.root}/compose.yaml', 'down', '--volumes', '--remove-orphans']],
        )
        self.assertIn(['volume', 'rm', 'leftover'], commands)
        self.assertFalse(state.exists())
        self.assertIn('Removed deployment raicho', result.stdout)

    def test_the_selected_project_and_state_directory_are_used(self):
        state = self.directory / 'state'
        (state / 'credentials').mkdir(parents=True)
        commands, _ = self.deploy_clean(
            *deployment('second'),
            answer='second\n',
            RAICHO_PROJECT='second',
            COMPOSE_PROJECT_NAME='ignored',
            RAICHO_STATE_DIRECTORY=str(state),
        )
        self.assertEqual(down(commands)[0][:3], ['compose', '-p', 'second'])
        self.assertFalse(state.exists())

    def test_invalid_selections_are_refused(self):
        for environment in ({'RAICHO_PROJECT': 'Bad Name'}, {'RAICHO_STATE_DIRECTORY': 'relative'}):
            with self.subTest(environment=environment):
                commands, result = self.deploy_clean(answer='raicho\n', status=1, **environment)
                self.assertEqual(commands, [])
                self.assertIn('FAIL: invalid project', result.stderr)

    def test_nothing_to_remove_needs_no_confirmation(self):
        commands, result = self.deploy_clean()
        self.assertEqual(down(commands), [])
        self.assertIn('Deployment raicho has nothing to remove', result.stdout)


if __name__ == '__main__':
    unittest.main()
