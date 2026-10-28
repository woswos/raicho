import fcntl
import os
import shutil
import subprocess
import time
import unittest

from automation.testing.docker_mock import DockerMock, Response
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

    def state(self, relative='.raicho/raicho', project='raicho'):
        directory = self.root / relative
        (directory / 'credentials').mkdir(parents=True)
        (directory / 'credentials/connector.token').write_text('secret\n')
        (directory / 'project').write_text(f'{project}\n')
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
        state = self.state('../state', 'second')
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
        self.assertIn(f'type=bind,source={state / "credentials"},target=/state', removal)
        self.assertIn('raicho-tools:local', removal)
        self.assertNotIn('rm', {command[1] for command in commands if len(command) > 1 and command[0] == 'volume'})
        self.assertIn('run make deploy-clean again', result.stderr)

    def test_the_operation_lock_outlives_the_volumes(self):
        state = self.state()
        self.deploy_clean(
            *deployment(),
            Response(('volume', '--quiet', f'{PROJECT_FILTER}raicho'), output='raicho_raicho-data\n'),
            Response(('volume', 'rm', 'raicho_raicho-data'), status=1),
            answer='raicho\n',
            status=1,
        )
        self.assertEqual([path.name for path in state.iterdir()], ['operation.lock'])

    def test_a_failed_removal_listing_keeps_the_lock_and_fails(self):
        state = self.state()
        _, result = self.deploy_clean(
            *deployment(),
            Response(('volume', '--quiet', f'{PROJECT_FILTER}raicho'), status=1),
            answer='raicho\n',
            status=1,
        )
        self.assertIn('FAIL:', result.stderr)
        self.assertEqual([path.name for path in state.iterdir()], ['operation.lock'])

    def test_a_missing_state_directory_is_locked_before_removal(self):
        state = self.root / '.raicho/raicho'
        self.deploy_clean(*deployment(), Response(('compose', 'down'), status=1), answer='raicho\n', status=1)
        self.assertEqual([path.name for path in state.iterdir()], ['operation.lock'])

    def test_nested_deployment_state_is_refused_before_listing(self):
        state = self.state()
        nested = state / 'credentials/nested'
        nested.mkdir()
        (nested / 'operation.lock').write_text('')
        (nested / 'connector.token').write_text('nested secret\n')
        commands, result = self.deploy_clean(*deployment(), answer='raicho\n', status=1)
        self.assertIn("holds another deployment's state", result.stderr)
        self.assertEqual(commands, [])
        self.assertTrue((nested / 'connector.token').exists())

    def test_an_unreadable_directory_of_the_caller_stops_the_scan(self):
        state = self.state()
        hidden = state / 'hidden'
        (hidden / 'nested').mkdir(parents=True)
        (hidden / 'nested/operation.lock').write_text('')
        hidden.chmod(0o111)
        self.addCleanup(hidden.chmod, 0o700)
        commands, result = self.deploy_clean(*deployment(), answer='raicho\n', status=1)
        self.assertIn('could not inspect', result.stderr)
        self.assertEqual(commands, [])

    def test_a_failed_docker_listing_stops_before_reporting_or_cleaning(self):
        commands, result = self.deploy_clean(
            Response(('container', '--format', '{{.Names}}', f'{PROJECT_FILTER}raicho'), status=1), status=1
        )
        self.assertIn("FAIL: could not list the deployment's containers", result.stderr)
        self.assertNotIn('nothing to remove', result.stdout)
        self.assertNotIn(CACHE_REMOVAL, commands)

    def test_nothing_to_remove_needs_no_confirmation_and_still_cleans(self):
        commands, result = self.deploy_clean()
        self.assertEqual(compose(commands), [])
        self.assertIn(CACHE_REMOVAL, commands)
        self.assertIn('Deployment raicho has nothing to remove', result.stdout)
        self.assertFalse((self.root / '.raicho/raicho').exists())

    def test_state_of_another_or_no_project_is_refused_before_listing(self):
        for marker in ('other\n', None):
            with self.subTest(marker=marker):
                state = self.state()
                if marker is None:
                    (state / 'project').unlink()
                else:
                    (state / 'project').write_text(marker)
                commands, result = self.deploy_clean(*deployment(), answer='raicho\n', status=1)
                self.assertIn('is not marked as the state of raicho', result.stderr)
                self.assertEqual(commands, [])
                self.assertTrue((state / 'credentials/connector.token').exists())
                shutil.rmtree(state)

    def test_a_cancel_leaves_no_new_state_directory(self):
        self.deploy_clean(*deployment(), answer='no\n', status=1)
        self.assertFalse((self.root / '.raicho/raicho').exists())

    def test_a_held_state_lock_blocks_deploy_clean(self):
        layout = self.temporary / f'raicho-state-{os.getuid()}'
        layout.mkdir(mode=0o700)
        with (layout / 'layout.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            commands, result = self.deploy_clean(*deployment(), answer='raicho\n', status=1)
        self.assertEqual(commands, [])
        self.assertIn('another credential or deploy-clean command', result.stderr)

    def test_a_credential_command_cannot_claim_state_during_the_prompt(self):
        state = self.root / '.raicho/raicho'
        docker = DockerMock(self.directory / 'commands', deployment())
        cleaner = subprocess.Popen(
            ['bash', str(self.root / 'automation/tooling/deploy_clean.bash')],
            env=docker.environment(TMPDIR=str(self.temporary)),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.addCleanup(cleaner.kill)
        deadline = time.monotonic() + 10
        while not any(command[:2] == ['volume', 'ls'] for command in docker.commands()):
            self.assertLess(time.monotonic(), deadline, 'deploy-clean never listed the deployment')
            time.sleep(0.05)
        wrapper = subprocess.run(
            ['bash', str(self.root / 'deploy/credentials/connector.bash'), 'status'],
            env=docker.environment(
                TMPDIR=str(self.temporary), RAICHO_PROJECT='raicho-child', RAICHO_STATE_DIRECTORY=str(state / 'child')
            ),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(wrapper.returncode, 0)
        self.assertIn("inside another deployment's state", wrapper.stderr)
        self.assertFalse((state / 'child').exists())
        cleaner.communicate('no\n', timeout=10)
        self.assertEqual(cleaner.returncode, 1)
        self.assertFalse(state.exists())


if __name__ == '__main__':
    unittest.main()
