import unittest
from pathlib import Path

import yaml

WORKFLOW = (
    Path(__file__).resolve().parents[1] / '.github/workflows/repository-checks.yml'
)


class WorkflowCoverageTests(unittest.TestCase):
    def setUp(self):
        self.jobs = yaml.load(WORKFLOW.read_text(), Loader=yaml.BaseLoader)['jobs']

    def test_ci_runs_all_unattended_connector_acceptance_commands(self):
        expected = {
            'connector-test': (
                'bash devbin/raicho_check_connector.bash',
                'bash devbin/raicho_check_credentials.bash',
            ),
            'compatibility-test': (
                'bash devbin/raicho_check_extension_lifecycle.bash',
                'bash devbin/raicho_check_mail_compatibility.bash',
            ),
        }
        for name, commands in expected.items():
            with self.subTest(job=name):
                job = self.jobs[name]
                script = '\n'.join(step.get('run', '') for step in job['steps'])
                for command in commands:
                    self.assertIn(command, script)
                self.assertNotIn('--native', script)
                self.assertEqual(job['if'], self.jobs['runtime-test']['if'])
                self.assertNotIn('needs', job)
                self.assertGreaterEqual(int(job['timeout-minutes']), 45)

    def test_application_job_tests_both_production_and_mail_probe_sources(self):
        script = '\n'.join(
            step.get('run', '') for step in self.jobs['application-test']['steps']
        )
        self.assertIn('make build-app test-app test-mail-probe test-protocol', script)
        self.assertIn('PYTHONPATH=/workspace/runtime/thunderbird', script)
        self.assertIn('unittest discover -s runtime/thunderbird/tests', script)

    def test_image_job_validates_the_production_credential_override(self):
        script = '\n'.join(
            step.get('run', '') for step in self.jobs['application-build']['steps']
        )
        self.assertIn('-f compose/compose.credentials.yaml config --quiet', script)

    def test_image_job_validates_the_disposable_fixture_configurations(self):
        script = '\n'.join(
            step.get('run', '') for step in self.jobs['application-build']['steps']
        )
        for configuration in (
            '-f compose/compose.extension_test.yaml',
            '-f compose/compose.mail_test.yaml',
            '-f compose/compose.mail_test.yaml -f compose/compose.mail_admin.yaml',
        ):
            self.assertIn(f'{configuration} --profile test config --quiet', script)

    def test_runtime_job_uses_the_runtime_test_override(self):
        self.assertEqual(
            self.jobs['runtime-test']['env']['COMPOSE_FILE'],
            'compose/compose.yaml:compose/compose.runtime_test.yaml',
        )
        script = '\n'.join(
            step.get('run', '') for step in self.jobs['application-build']['steps']
        )
        self.assertIn(
            '-f compose/compose.yaml -f compose/compose.runtime_test.yaml config --quiet',
            script,
        )
