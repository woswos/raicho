import subprocess
import unittest

import yaml

from automation.paths import REPOSITORY_ROOT

WORKFLOW = REPOSITORY_ROOT / '.github/workflows/repository-checks.yml'
PULL_REQUEST_EVENT = "${{ github.event_name == 'pull_request' }}"


class WorkflowCoverageTests(unittest.TestCase):
    def setUp(self):
        self.text = WORKFLOW.read_text()
        self.jobs = yaml.load(self.text, Loader=yaml.BaseLoader)['jobs']

    def script(self, *names):
        return '\n'.join(
            step.get('run', '') for name in names for step in self.jobs[name]['steps']
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
        for target in ('build-app', 'test-app'):
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
