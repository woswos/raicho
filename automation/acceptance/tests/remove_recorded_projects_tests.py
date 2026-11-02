import os
import signal
import subprocess
import tempfile
import unittest
from pathlib import Path

from automation.acceptance.tests.process_fixture import kill, start_time, stopped
from automation.paths import REPOSITORY_ROOT
from automation.testing.docker_mock import DockerMock, Response

REMOVAL = REPOSITORY_ROOT / 'automation/acceptance/remove_recorded_projects.bash'
PROJECT = 'raicho-connector-20261101120000-42'
PROJECT_FILTER = f'label=com.docker.compose.project={PROJECT}'


def entry(runner, project=PROJECT, state=''):
    start = start_time(runner.pid)
    return (runner.pid, start, runner.pid, start, project, state)


class RemoveRecordedProjectsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-record-test-')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.record = self.directory / 'record'

    def runner(self):
        runner = subprocess.Popen(['sleep', '60'], start_new_session=True)
        self.addCleanup(runner.wait)
        self.addCleanup(runner.kill)
        return runner

    def remove(self, entries, *responses, status=0):
        if entries is not None:
            self.record.write_text(''.join('\t'.join(map(str, entry)) + '\n' for entry in entries))
        docker = DockerMock(tempfile.mkdtemp(dir=self.directory), responses)
        result = subprocess.run(
            ['bash', str(REMOVAL)],
            env=docker.environment(RAICHO_ACCEPTANCE_RECORD=str(self.record)),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, status, result.stderr)
        return docker.commands(), result

    def test_stops_the_runner_and_removes_only_its_project(self):
        runner = self.runner()
        commands, _ = self.remove(
            [entry(runner)],
            Response(('container', 'ls', '--quiet', PROJECT_FILTER), output='probe-id\nserver-id\n'),
            Response(('container', 'inspect', '--format'), output='true probe-id\nfalse server-id\n'),
            Response(('container', 'inspect'), status=1),
            Response(('volume', 'ls', '--quiet', PROJECT_FILTER), output='volume-id\n'),
            Response(('network', 'ls', '--quiet', PROJECT_FILTER), output='network-id\n'),
            Response(('image', 'ls'), output=f'{PROJECT}:tools\n'),
        )
        self.assertEqual(runner.wait(timeout=10), -signal.SIGKILL)
        containers = commands.index(['container', 'rm', 'server-id'])
        self.assertLess(commands.index(['container', 'stop', 'probe-id', 'server-id']), containers)
        self.assertLess(containers, commands.index(['volume', 'rm', 'volume-id']))
        self.assertLess(containers, commands.index(['network', 'rm', 'network-id']))
        self.assertIn(['image', 'rm', f'{PROJECT}:tools'], commands)
        filters = {word for command in commands for word in command if word.startswith(('label=', 'reference='))}
        self.assertEqual(filters, {PROJECT_FILTER, f'reference={PROJECT}:*'})

    def test_removes_the_recorded_state_directory(self):
        state = self.directory / 'raicho-credentials.Ab3dE5gH'
        (state / 'credentials').mkdir(parents=True)
        (state / 'credentials/connector.token').write_text('secret\n')
        runner = self.runner()
        self.remove([entry(runner, 'raicho-credentials-20261101120000-7', state)])
        self.assertFalse(state.exists())

    def test_leaves_a_process_group_without_the_recorded_leader_or_runner(self):
        runner = self.runner()
        for start in ('0', str(int(start_time(runner.pid)) + 1)):
            with self.subTest(start=start):
                self.remove([(runner.pid, start, runner.pid, start, PROJECT, '')])
                self.assertIsNone(runner.poll())

    def test_stops_a_runner_whose_group_leader_exited(self):
        leader = subprocess.Popen(
            ['bash', '-c', 'sleep 60 & echo "$!"'], start_new_session=True, stdout=subprocess.PIPE, text=True
        )
        worker = int(leader.stdout.readline())
        self.addCleanup(kill, worker)
        leader.wait()
        leader.stdout.close()
        self.remove([(leader.pid, '1', worker, start_time(worker), PROJECT, '')])
        self.assertTrue(stopped(worker))

    def test_does_nothing_without_a_record(self):
        commands, _ = self.remove(None)
        self.assertEqual(commands, [])

    def test_refuses_entries_that_could_reach_another_process_or_project(self):
        elsewhere = Path(tempfile.mkdtemp(dir=self.directory)) / 'raicho-credentials.Ab3dE5gH'
        entries = {
            'no process group': (0, None, PROJECT, ''),
            'non-numeric process group': ('1x', None, PROJECT, ''),
            'own process group': (os.getpgrp(), None, PROJECT, ''),
            'non-numeric runner': (None, '1x', PROJECT, ''),
            'persistent project': (None, None, 'raicho', ''),
            'foreign directory': (None, None, PROJECT, self.directory),
            'state directory away from the record': (None, None, PROJECT, elsewhere),
        }
        for case, (group, worker, project, state) in entries.items():
            with self.subTest(case=case):
                runner = self.runner()
                start = start_time(runner.pid)
                group = runner.pid if group is None else group
                worker = runner.pid if worker is None else worker
                commands, result = self.remove([(group, start, worker, start, project, state)], status=1)
                self.assertEqual(commands, [])
                self.assertIsNone(runner.poll())
                self.assertIn('FAIL', result.stderr)

    def test_removes_networks_after_a_failed_volume_removal(self):
        runner = self.runner()
        commands, _ = self.remove(
            [entry(runner)],
            Response(('volume', 'ls', '--quiet', PROJECT_FILTER), output='volume-id\n'),
            Response(('volume', 'rm'), status=1),
            Response(('network', 'ls', '--quiet', PROJECT_FILTER), output='network-id\n'),
            status=1,
        )
        self.assertIn(['network', 'rm', 'network-id'], commands)

    def test_reports_a_project_it_could_not_remove(self):
        failures = {
            'volume': (
                Response(('volume', 'ls', '--quiet', PROJECT_FILTER), output='volume-id\n'),
                Response(('volume', 'rm'), status=1),
            ),
            'image': (
                Response(('image', 'ls'), output=f'{PROJECT}:tools\n'),
                Response(('image', 'rm'), status=1),
            ),
        }
        state = self.directory / 'raicho-connector.Ab3dE5gH'
        for kind, responses in failures.items():
            with self.subTest(kind=kind):
                (state / 'credentials').mkdir(parents=True, exist_ok=True)
                (state / 'credentials/connector.token').write_text('secret\n')
                runner = self.runner()
                _, result = self.remove([entry(runner, state=state)], *responses, status=1)
                self.assertIn(PROJECT, result.stderr)
                self.assertFalse(state.exists())


if __name__ == '__main__':
    unittest.main()
