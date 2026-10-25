import subprocess
import unittest

import yaml

from automation.paths import REPOSITORY_ROOT

WORKFLOW = REPOSITORY_ROOT / '.github/workflows/repository-checks.yml'
ACCEPTANCE_JOBS = ('connector-test', 'compatibility-test')


class WorkflowCoverageTests(unittest.TestCase):
    def setUp(self):
        self.text = WORKFLOW.read_text()
        self.jobs = yaml.load(self.text, Loader=yaml.BaseLoader)['jobs']

    def script(self, *names):
        return '\n'.join(
            step.get('run', '') for name in names for step in self.jobs[name]['steps']
        )

    def test_every_acceptance_runner_runs_unattended_in_an_independent_job(self):
        runners = sorted(
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for directory in ('automation/acceptance', 'mailprobe')
            for path in (REPOSITORY_ROOT / directory).rglob('check_*.bash')
            if path.name != 'check_admin_isolation.bash'
        )
        self.assertTrue(runners)
        script = self.script(*ACCEPTANCE_JOBS)
        for runner in runners:
            with self.subTest(runner=runner):
                self.assertIn(f'bash {runner}', script)
        self.assertNotIn('--native', script)
        for name in ACCEPTANCE_JOBS:
            with self.subTest(job=name):
                job = self.jobs[name]
                self.assertEqual(job['if'], self.jobs['runtime-test']['if'])
                self.assertNotIn('needs', job)

    def test_every_compose_file_is_exercised(self):
        paths = subprocess.run(
            ['git', 'ls-files', '*compose*.yaml'],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.split()
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(file=path):
                self.assertIn(f'-f {path}', self.text)

    def test_application_job_runs_every_source_suite(self):
        words = set(self.script('application-test').split())
        for target in ('build-app', 'test-app', 'test-mailprobe', 'test-protocol'):
            with self.subTest(target=target):
                self.assertIn(target, words)
        self.assertIn('deploy/thunderbird/tests', words)
