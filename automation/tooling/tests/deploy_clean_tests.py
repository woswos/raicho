import fcntl
import os
import unittest

from automation.testing.docker_mock import Response
from automation.tooling.tests.cleanup_fixture import PROJECT_FILTER, CleanupFixture

NAMES = '{{.Name}}'
CACHE_REMOVAL = ['volume', 'rm', 'raicho-tools_cache']


def deployment(project='raicho'):
    return (
        Response(
            ('container', '--format', '{{.Names}}', f'{PROJECT_FILTER}{project}'), output=f'{project}-thunderbird-1\n'
        ),
        Response(('network', '--format', NAMES, f'{PROJECT_FILTER}{project}'), output=f'{project}_application\n'),
        Response(('volume', '--format', NAMES, f'{PROJECT_FILTER}{project}'), output=f'{project}_thunderbird-data\n'),
    )


def compose(commands):
    return [command for command in commands if command[:1] == ['compose']]


class DeployCleanTests(CleanupFixture):
    def deploy_clean(self, *responses, **options):
        return self.run_script('deploy_clean.bash', *responses, **options)

    def state(self, relative='.raicho/raicho'):
        directory = self.root / relative
        (directory / 'credentials').mkdir(parents=True)
        (directory / 'credentials/connector.token').write_text('secret\n')
        directory.chmod(0o700)
        return directory

    def test_a_wrong_or_missing_answer_removes_nothing(self):
        state = self.state()
        leftover = self.write('target/debug/raicho-server')
        for answer in ('', 'yes\n', 'raicho-second\n'):
            with self.subTest(answer=answer):
                commands, result = self.deploy_clean(*deployment(), answer=answer, status=1)
                self.assertEqual(compose(commands), [])
                self.assertNotIn(CACHE_REMOVAL, commands)
                self.assertTrue(leftover.exists())
                self.assertTrue((state / 'credentials/connector.token').exists())
                self.assertIn('Cancelled. Nothing was removed.', result.stderr)
                for line in ('network raicho_application', 'volume raicho_thunderbird-data'):
                    self.assertIn(line, result.stdout)

    def test_the_project_name_confirms_the_removal_then_cleans(self):
        state = self.state()
        leftover = self.write('target/debug/raicho-server')
        commands, result = self.deploy_clean(
            *deployment(),
            Response(('volume', '--quiet', f'{PROJECT_FILTER}raicho'), output='leftover-volume\n'),
            Response(('network', '--quiet', f'{PROJECT_FILTER}raicho'), output='leftover-network\n'),
            answer='raicho\n',
        )
        self.assertEqual(
            compose(commands),
            [['compose', '-p', 'raicho', '-f', f'{self.root}/compose.yaml', 'down', '--remove-orphans']],
        )
        self.assertIn(['volume', 'rm', 'leftover-volume'], commands)
        self.assertIn(['network', 'rm', 'leftover-network'], commands)
        self.assertFalse(state.exists())
        self.assertIn('Removed deployment raicho', result.stdout)
        self.assertGreater(commands.index(CACHE_REMOVAL), commands.index(['volume', 'rm', 'leftover-volume']))
        self.assertFalse(leftover.exists())

    def test_the_selected_project_and_state_directory_are_used(self):
        state = self.state('../state')
        commands, _ = self.deploy_clean(
            *deployment('second'),
            answer='second\n',
            RAICHO_PROJECT='second',
            COMPOSE_PROJECT_NAME='ignored',
            RAICHO_STATE_DIRECTORY=str(state.resolve()),
        )
        self.assertEqual(compose(commands)[0][:3], ['compose', '-p', 'second'])
        self.assertFalse(state.exists())

    def test_unsafe_selections_are_refused_before_listing(self):
        shared = self.directory / 'shared'
        shared.mkdir(mode=0o755)
        link = self.directory / 'link'
        link.symlink_to(self.state())
        cases = (
            ({'RAICHO_PROJECT': 'Bad Name'}, 'invalid project'),
            ({'RAICHO_PROJECT': 'raicho-tools'}, 'invalid project'),
            ({'RAICHO_STATE_DIRECTORY': 'relative'}, 'invalid project'),
            ({'RAICHO_STATE_DIRECTORY': str(shared)}, 'must be a private directory'),
            ({'RAICHO_STATE_DIRECTORY': str(link)}, 'must be a private directory'),
        )
        for environment, message in cases:
            with self.subTest(environment=environment):
                commands, result = self.deploy_clean(answer='raicho\n', status=1, **environment)
                self.assertEqual(commands, [])
                self.assertIn(message, result.stderr)

    def test_a_running_credential_operation_blocks_the_removal(self):
        state = self.state()
        with (state / 'operation.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            commands, result = self.deploy_clean(*deployment(), answer='raicho\n', status=1)
        self.assertEqual(compose(commands), [])
        self.assertIn('a credential operation is running', result.stderr)
        self.assertTrue(state.exists())

    @unittest.skipIf(os.geteuid() == 0, 'root ignores directory permissions')
    def test_a_kept_state_directory_keeps_the_volumes(self):
        state = self.state()
        (state / 'credentials').chmod(0o500)
        self.addCleanup((state / 'credentials').chmod, 0o700)
        commands, result = self.deploy_clean(*deployment(), answer='raicho\n', status=1)
        removal = next(command for command in commands if command[:1] == ['run'])
        self.assertIn(f'type=bind,source={state},target=/state', removal)
        self.assertIn('raicho-tools:local', removal)
        self.assertNotIn('rm', {command[1] for command in commands if len(command) > 1 and command[0] == 'volume'})
        self.assertIn('run make deploy-clean again', result.stderr)

    def test_nothing_to_remove_needs_no_confirmation_and_still_cleans(self):
        commands, result = self.deploy_clean()
        self.assertEqual(compose(commands), [])
        self.assertIn(CACHE_REMOVAL, commands)
        self.assertIn('Deployment raicho has nothing to remove', result.stdout)


if __name__ == '__main__':
    unittest.main()
