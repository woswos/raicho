import subprocess
import unittest

import yaml

from automation.paths import REPOSITORY_ROOT

WORKFLOW = REPOSITORY_ROOT / '.github/workflows/repository-checks.yml'
PULL_REQUEST_EVENT = "${{ github.event_name == 'pull_request' }}"
ACCEPTANCE_JOBS = ('connector-test',)


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
            for directory in ('automation/acceptance',)
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

    def test_acceptance_state_stays_where_the_docker_host_can_bind_it(self):
        for step in self.jobs['connector-test']['steps']:
            if 'name' in step:
                with self.subTest(step=step['name']):
                    self.assertEqual(
                        step.get('env', {}).get('TMPDIR'), '${{ runner.temp }}'
                    )

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
        for target in ('build-app', 'test-app', 'test-protocol'):
            with self.subTest(target=target):
                self.assertIn(target, words)

    def test_newer_pull_request_runs_cancel_older_ones(self):
        for path in sorted(WORKFLOW.parent.glob('*.yml')):
            workflow = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
            if 'pull_request' not in workflow['on']:
                continue
            with self.subTest(workflow=path.name):
                concurrency = workflow['concurrency']
                self.assertIn('github.event.pull_request.number', concurrency['group'])
                cancels = concurrency['cancel-in-progress']
                self.assertIn(cancels, ('true', PULL_REQUEST_EVENT))

    def test_lint_job_runs_every_python_suite(self):
        self.assertIn('test-python', self.script('lint').split())
