import re
import subprocess
import unittest

import yaml

from automation.paths import REPOSITORY_ROOT

WORKFLOW = REPOSITORY_ROOT / '.github/workflows/repository-checks.yml'
PULL_REQUEST_EVENT = "${{ github.event_name == 'pull_request' }}"
GUARD_WORKFLOW = REPOSITORY_ROOT / '.github/workflows/pull-request-guards.yml'
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
CACHE_DIRECTORY = '${{ runner.temp }}/raicho-cache'
ACCEPTANCE_RECORD = '${{ runner.temp }}/raicho-acceptance'
CODE_EVENTS = {'opened', 'synchronize', 'reopened'}
METADATA_EVENTS = {'edited', 'labeled', 'unlabeled', 'ready_for_review', 'converted_to_draft'}


def pull_request_events(workflow):
    triggers = workflow['on']['pull_request']
    # Without a types list, GitHub runs pull_request workflows on its default events.
    return set((triggers or {}).get('types', CODE_EVENTS))


class WorkflowCoverageTests(unittest.TestCase):
    def setUp(self):
        self.text = WORKFLOW.read_text()
        self.workflow = yaml.load(self.text, Loader=yaml.BaseLoader)
        self.jobs = self.workflow['jobs']

    def script(self, *names):
        return '\n'.join(step.get('run', '') for name in names for step in self.jobs[name]['steps'])

    def test_every_acceptance_runner_runs_unattended_in_an_independent_job(self):
        runners = sorted(
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for directory, pattern in (('automation/acceptance', 'run.bash'), ('mailprobe', 'check_*.bash'))
            for path in (REPOSITORY_ROOT / directory).rglob(pattern)
        )
        self.assertTrue(runners)
        recipes = HOST_MAKEFILE.read_text().replace('$(ACCEPTANCE) $@ ', '').replace('$(REPOSITORY_ROOT)', '')
        targets = {
            target
            for target, recipe in re.findall(r'^(acceptance-[a-z]+):\n\t@(.*)$', recipes, re.MULTILINE)
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

    def test_acceptance_state_stays_where_the_docker_host_can_bind_it(self):
        for step in self.jobs['connector-test']['steps']:
            if 'make acceptance-' in step.get('run', ''):
                with self.subTest(step=step['name']):
                    self.assertEqual(step.get('env', {}).get('TMPDIR'), '${{ runner.temp }}')

    def test_acceptance_jobs_remove_their_recorded_projects_even_when_cancelled(self):
        for name in ACCEPTANCE_JOBS:
            with self.subTest(job=name):
                *runners, removal = [step for step in self.jobs[name]['steps'] if 'run' in step]
                self.assertTrue(runners)
                for step in runners:
                    self.assertRegex(step['run'], r'^setsid --wait make acceptance-[a-z]+$')
                    self.assertEqual(step['env']['RAICHO_ACCEPTANCE_RECORD'], ACCEPTANCE_RECORD)
                self.assertEqual(removal['if'], 'always()')
                self.assertEqual(removal['run'], 'bash automation/acceptance/remove_recorded_projects.bash')
                self.assertEqual(removal['env']['RAICHO_ACCEPTANCE_RECORD'], ACCEPTANCE_RECORD)

    def test_every_compose_file_is_exercised(self):
        paths = subprocess.run(
            ['git', 'ls-files', '*compose*.yaml'],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.split()
        self.assertTrue(paths)
        commands = self.text + HOST_MAKEFILE.read_text().replace('$(REPOSITORY_ROOT)', '')
        for path in paths:
            with self.subTest(file=path):
                self.assertIn(f'-f {path}', commands)

    def test_application_job_runs_every_source_suite(self):
        self.assertIn('make test', self.script('application-test'))
        aggregate = next(line for line in CONTAINER_MAKEFILE.read_text().splitlines() if line.startswith('test:'))
        for target in SOURCE_SUITES:
            with self.subTest(target=target):
                self.assertIn(target, aggregate.split())

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

    def test_only_the_guard_reruns_on_description_and_label_changes(self):
        guard = yaml.load(GUARD_WORKFLOW.read_text(), Loader=yaml.BaseLoader)
        self.assertEqual(set(guard['jobs']), {'pr-guards'})
        self.assertEqual(pull_request_events(guard), CODE_EVENTS | METADATA_EVENTS)
        self.assertEqual(pull_request_events(self.workflow), CODE_EVENTS)
        self.assertNotIn('pr-guards', self.jobs)

    def test_lint_job_runs_every_python_suite(self):
        self.assertIn('test-python', self.script('lint').split())

    def coverage_steps(self):
        return {step['run']: step.get('if') for step in self.jobs['coverage']['steps'] if 'run' in step}

    def test_coverage_job_gates_pull_requests_on_changed_lines(self):
        job = self.jobs['coverage']
        for label in ('design', 'skip-test', 'skip-coverage-check'):
            with self.subTest(label=label):
                self.assertIn(f"'{label}'", job['if'])
        self.assertEqual(job['steps'][0]['with']['fetch-depth'], '0')
        self.assertEqual(self.coverage_steps()['make check-patch-coverage'], "github.event_name == 'pull_request'")

    def test_pushes_to_main_save_the_coverage_cache_for_pull_requests(self):
        self.assertNotIn('event_name', self.jobs['coverage']['if'])
        # actions/cache saves nothing after an exact key hit, so the build would be wasted then.
        cache = next(
            step for step in self.jobs['coverage']['steps'] if step.get('uses', '').startswith('actions/cache@')
        )
        self.assertEqual(
            self.coverage_steps()['make coverage'],
            f"github.event_name == 'push' && steps.{cache['id']}.outputs.cache-hit != 'true'",
        )

    def test_rust_building_jobs_restore_their_cargo_cache(self):
        # The runner shares only its work directory with the Docker host, so the folder must live there.
        self.assertNotIn('RAICHO_CACHE_DIRECTORY', self.workflow.get('env', {}))
        for name in ('lint', 'application-test', 'coverage'):
            with self.subTest(job=name):
                steps = self.jobs[name]['steps']
                cache = next(step for step in steps if step.get('uses', '').startswith('actions/cache@'))
                self.assertEqual(cache['with']['path'], CACHE_DIRECTORY)
                for step in steps:
                    if 'make ' in step.get('run', ''):
                        self.assertEqual(step['env']['RAICHO_CACHE_DIRECTORY'], CACHE_DIRECTORY)
                self.assertIn("hashFiles('Cargo.lock', 'rust-toolchain.toml')", cache['with']['key'])
