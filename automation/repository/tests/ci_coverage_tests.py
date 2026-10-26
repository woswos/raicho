import re
import subprocess
import unittest

import yaml

from automation.paths import REPOSITORY_ROOT

WORKFLOW = REPOSITORY_ROOT / '.github/workflows/repository-checks.yml'
HOST_MAKEFILE = REPOSITORY_ROOT / 'automation/tooling/host.mk'
CONTAINER_MAKEFILE = REPOSITORY_ROOT / 'automation/tooling/container.mk'
SOURCE_SUITES = (
    'test-python',
    'test-tooling',
    'test-server',
    'test-web',
    'test-extension',
    'test-mailprobe',
    'test-protocol',
)
ACCEPTANCE_JOBS = ('runtime-test', 'connector-test', 'compatibility-test')


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
        recipes = (
            HOST_MAKEFILE.read_text()
            .replace('$(ACCEPTANCE)', 'bash $(REPOSITORY_ROOT)')
            .replace('$(REPOSITORY_ROOT)', '')
        )
        targets = {
            target
            for target, recipe in re.findall(
                r'^(acceptance-[a-z]+):\n\t@(.*)$', recipes, re.MULTILINE
            )
            if any(recipe == f'bash {runner}' for runner in runners)
        }
        self.assertEqual(len(targets), len(runners))
        script = self.script(*ACCEPTANCE_JOBS)
        for target in sorted(targets):
            with self.subTest(target=target):
                self.assertIn(f'make {target}', script)
        self.assertNotIn('--native', script + recipes)
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
        commands = self.text + HOST_MAKEFILE.read_text().replace(
            '$(REPOSITORY_ROOT)', ''
        )
        for path in paths:
            with self.subTest(file=path):
                self.assertIn(f'-f {path}', commands)

    def test_application_job_runs_every_source_suite(self):
        self.assertIn('make test', self.script('application-test'))
        aggregate = next(
            line
            for line in CONTAINER_MAKEFILE.read_text().splitlines()
            if line.startswith('test:')
        )
        for target in SOURCE_SUITES:
            with self.subTest(target=target):
                self.assertIn(target, aggregate.split())

    def test_lint_job_runs_every_python_suite(self):
        self.assertIn('test-python', self.script('lint').split())

    def test_coverage_job_gates_pull_requests_on_changed_lines(self):
        job = self.jobs['coverage']
        self.assertIn("github.event_name == 'pull_request'", job['if'])
        for label in ('design', 'skip-test', 'skip-coverage-check'):
            with self.subTest(label=label):
                self.assertIn(f"'{label}'", job['if'])
        self.assertEqual(job['steps'][0]['with']['fetch-depth'], '0')
        self.assertIn('make check-patch-coverage', self.script('coverage'))
