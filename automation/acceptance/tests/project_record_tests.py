import os
import shlex
import subprocess
import tempfile
import unittest
from pathlib import Path

from automation.acceptance.tests.process_fixture import start_time
from automation.paths import REPOSITORY_ROOT

RECORDER = REPOSITORY_ROOT / 'automation/acceptance/project_record.bash'
PROJECT = 'raicho-connector-20261101120000-42'


class ProjectRecordTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-record-test-')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.record = self.directory / 'record'

    def record_project(self, *arguments, **variables):
        inherited = {name: value for name, value in os.environ.items() if name != 'RAICHO_ACCEPTANCE_RECORD'}
        script = f'source {shlex.quote(str(RECORDER))}\nrecord_project "$@"\necho "$$"'
        return subprocess.run(
            ['bash', '-euo', 'pipefail', '-c', script, 'record', *arguments],
            env=inherited | variables,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def test_records_the_runner_process_group_with_its_project(self):
        state = '/tmp/raicho-connector.Ab3dE5gH'
        workers = [
            self.record_project(PROJECT, state, RAICHO_ACCEPTANCE_RECORD=str(self.record)),
            self.record_project('raicho-ci-123-1', RAICHO_ACCEPTANCE_RECORD=str(self.record)),
        ]
        group = os.getpgrp()
        lines = [line.split('\t') for line in self.record.read_text().splitlines()]
        self.assertEqual(
            [fields[:3] for fields in lines], [[str(group), start_time(group), worker] for worker in workers]
        )
        self.assertTrue(all(fields[3].isdigit() and fields[3] != '0' for fields in lines))
        self.assertEqual([fields[4:] for fields in lines], [[PROJECT, state], ['raicho-ci-123-1', '']])

    def test_records_nothing_without_a_record_path(self):
        self.record_project(PROJECT)
        self.assertEqual(list(self.directory.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
