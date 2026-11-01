import os
import shlex
import signal
import subprocess
import tempfile
import unittest
from pathlib import Path

from automation.paths import REPOSITORY_ROOT
from automation.testing.docker_mock import DockerMock, Response

RECORDER = REPOSITORY_ROOT / 'automation/acceptance/project_record.bash'
REMOVAL = REPOSITORY_ROOT / 'automation/acceptance/remove_recorded_projects.bash'
PROJECT = 'raicho-connector-20261101120000-42'
PROJECT_FILTER = f'label=com.docker.compose.project={PROJECT}'
NETWORK = f'{PROJECT}_application'
VOLUME = f'{PROJECT}_raicho-data'


def start_time(process):
    try:
        status = Path(f'/proc/{process}/stat').read_text()
    except FileNotFoundError:
        return '0'
    return status.rsplit(') ', 1)[1].split()[19]


class RecordedProjectTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-record-test-')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.record = self.directory / 'record'

    def record_project(self, *arguments, **variables):
        inherited = {name: value for name, value in os.environ.items() if name != 'RAICHO_ACCEPTANCE_RECORD'}
        subprocess.run(
            ['bash', '-euo', 'pipefail', '-c', f'source {shlex.quote(str(RECORDER))}\nrecord_project "$@"', 'record']
            + list(arguments),
            env=inherited | variables,
            check=True,
        )

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

    def test_records_the_runner_process_group_with_its_project(self):
        state = '/tmp/raicho-connector.Ab3dE5gH'
        self.record_project(PROJECT, state, RAICHO_ACCEPTANCE_RECORD=str(self.record))
        self.record_project('raicho-ci-123-1', RAICHO_ACCEPTANCE_RECORD=str(self.record))
        group = os.getpgrp()
        identity = f'{group}\t{start_time(group)}'
        self.assertEqual(self.record.read_text(), f'{identity}\t{PROJECT}\t{state}\n{identity}\traicho-ci-123-1\t\n')

    def test_records_nothing_without_a_record_path(self):
        self.record_project(PROJECT)
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_stops_the_runner_and_removes_only_its_project(self):
        runner = self.runner()
        commands, _ = self.remove(
            [(runner.pid, start_time(runner.pid), PROJECT, '')],
            Response(('network', 'ls', '--format', PROJECT_FILTER), output=f'{NETWORK}\n'),
            Response(('volume', 'ls', '--format', PROJECT_FILTER), output=f'{VOLUME}\n'),
            Response(('container', 'ls', f'network={NETWORK}'), output='probe\nraicho\n'),
            Response(('container', 'ls', f'volume={VOLUME}'), output='raicho\nfixture\n'),
            Response(('volume', 'ls', '--quiet', PROJECT_FILTER), output='volume-id\n'),
            Response(('network', 'ls', '--quiet', PROJECT_FILTER), output='network-id\n'),
            Response(('image', 'ls'), output=f'{PROJECT}:tools\n'),
        )
        self.assertEqual(runner.wait(timeout=10), -signal.SIGKILL)
        attached = commands.index(['container', 'rm', '--force', 'fixture', 'probe', 'raicho'])
        self.assertLess(attached, commands.index(['volume', 'rm', 'volume-id']))
        self.assertLess(attached, commands.index(['network', 'rm', 'network-id']))
        self.assertIn(['image', 'rm', f'{PROJECT}:tools'], commands)
        filters = {word for command in commands for word in command if word.startswith(('label=', 'reference='))}
        self.assertEqual(filters, {PROJECT_FILTER, f'reference={PROJECT}:*'})

    def test_removes_the_recorded_state_directory(self):
        state = self.directory / 'raicho-credentials.Ab3dE5gH'
        (state / 'credentials').mkdir(parents=True)
        (state / 'credentials/connector.token').write_text('secret\n')
        runner = self.runner()
        self.remove([(runner.pid, start_time(runner.pid), 'raicho-credentials-20261101120000-7', state)])
        self.assertFalse(state.exists())

    def test_leaves_a_process_group_whose_leader_is_not_the_recorded_runner(self):
        runner = self.runner()
        for start in ('0', str(int(start_time(runner.pid)) + 1)):
            with self.subTest(start=start):
                self.remove([(runner.pid, start, PROJECT, '')])
                self.assertIsNone(runner.poll())

    def test_does_nothing_without_a_record(self):
        commands, _ = self.remove(None)
        self.assertEqual(commands, [])

    def test_refuses_entries_that_could_reach_another_process_or_project(self):
        elsewhere = Path(tempfile.mkdtemp(dir=self.directory)) / 'raicho-credentials.Ab3dE5gH'
        entries = {
            'no process group': (0, PROJECT, ''),
            'non-numeric process group': ('1x', PROJECT, ''),
            'own process group': (os.getpgrp(), PROJECT, ''),
            'persistent project': (None, 'raicho', ''),
            'foreign directory': (None, PROJECT, self.directory),
            'state directory away from the record': (None, PROJECT, elsewhere),
        }
        for case, (group, project, state) in entries.items():
            with self.subTest(case=case):
                runner = self.runner()
                group = runner.pid if group is None else group
                commands, result = self.remove([(group, start_time(runner.pid), project, state)], status=1)
                self.assertEqual(commands, [])
                self.assertIsNone(runner.poll())
                self.assertIn('FAIL', result.stderr)

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
                _, result = self.remove([(runner.pid, start_time(runner.pid), PROJECT, state)], *responses, status=1)
                self.assertIn(PROJECT, result.stderr)
                self.assertFalse(state.exists())


if __name__ == '__main__':
    unittest.main()
