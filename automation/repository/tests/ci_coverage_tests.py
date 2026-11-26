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
ACCEPTANCE_JOBS = ('runtime-test', 'connector-test', 'credentials-test', 'compatibility-test')
CACHE_DIRECTORY = '${{ runner.temp }}/raicho-cache'
ACCEPTANCE_RECORD = '${{ runner.temp }}/raicho-acceptance'
CODE_EVENTS = {'opened', 'synchronize', 'reopened'}
METADATA_EVENTS = {'edited', 'labeled', 'unlabeled', 'ready_for_review', 'converted_to_draft'}
DRAFT_SKIPPING_JOBS = (*ACCEPTANCE_JOBS, 'coverage')


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
                self.assertEqual(job['needs'], 'changes')

    def test_acceptance_state_stays_where_the_docker_host_can_bind_it(self):
        steps = self.jobs['connector-test']['steps'] + self.jobs['credentials-test']['steps']
        for step in steps:
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

    def test_lint_and_application_jobs_run_every_source_suite_once(self):
        scripts = self.script('lint', 'application-test').split()
        aggregate = next(line for line in CONTAINER_MAKEFILE.read_text().splitlines() if line.startswith('test:'))
        # The aggregate would rerun the suites the other job already ran.
        self.assertNotIn('make test\n', self.script('lint', 'application-test') + '\n')
        for target in SOURCE_SUITES:
            with self.subTest(target=target):
                self.assertIn(target, aggregate.split())
                self.assertEqual(scripts.count(target), 1)

    def test_image_building_jobs_restore_their_layers_before_building(self):
        for name, job in self.jobs.items():
            steps = job['steps']
            first_make = next((index for index, step in enumerate(steps) if 'make ' in step.get('run', '')), None)
            if first_make is None:
                continue
            restored = [
                step['with'] for step in steps[:first_make] if step.get('uses', '').startswith('docker/bake-action@')
            ]
            with self.subTest(job=name):
                self.assertIn('automation/tooling/compose.yaml', [layers['files'] for layers in restored])
                for layers in restored:
                    # Bake reads its definition from Git unless told to use the checkout.
                    self.assertEqual(layers['source'], '.')
                    self.assertIn('cache-from=type=gha', layers['set'])
                    self.assertIn('cache-to=type=gha', layers['set'])

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
        # Leaving draft starts the jobs that drafts skip.
        self.assertEqual(pull_request_events(self.workflow), CODE_EVENTS | {'ready_for_review'})
        self.assertNotIn('pr-guards', self.jobs)

    def test_drafts_and_documentation_changes_skip_the_expensive_jobs(self):
        self.assertNotIn('if', self.jobs['lint'])
        self.assertNotIn('needs', self.jobs['lint'])
        for name in (*DRAFT_SKIPPING_JOBS, 'application-test'):
            with self.subTest(job=name):
                job = self.jobs[name]
                self.assertEqual(job['needs'], 'changes')
                self.assertIn("needs.changes.outputs.code == 'true'", job['if'])
                skips_drafts = '!github.event.pull_request.draft' in job['if']
                self.assertEqual(skips_drafts, name in DRAFT_SKIPPING_JOBS)

    def test_pull_requests_shorten_only_the_idle_observation(self):
        seconds = {
            step['env']['RAICHO_IDLE_SECONDS']
            for step in self.jobs['connector-test']['steps']
            if 'RAICHO_IDLE_SECONDS' in step.get('env', {})
        }
        self.assertEqual(seconds, {"${{ github.event_name == 'pull_request' && '120' || '600' }}"})

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
