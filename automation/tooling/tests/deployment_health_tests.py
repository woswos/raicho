import json
import os
import subprocess
import sys
import tempfile
import unittest

from automation.paths import REPOSITORY_ROOT
from automation.tooling.deployment_health import commits_behind, report

DEPLOYED = 'f9b72381ff0701f17a254a44526409183f849c03'
CHECKOUT = '41dad8535dcc0b7bc1d6e48b1ad5eb7c4bd4d6aa'
IDENTITY = ('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid')


def status(application='ready', connector='connected', last_error=None, heartbeats=12, commit=DEPLOYED):
    return {
        'status': application,
        'database': {'status': application, 'engine': 'sqlite', 'version': '3.51.3'},
        'backend': {
            'kind': 'thunderbird',
            'status': connector,
            'generation': None,
            'last_error': last_error,
            'heartbeat_count': heartbeats,
        },
        'version': '0.1.0',
        'commit': commit,
    }


class DeploymentHealthReportTests(unittest.TestCase):
    def test_a_connected_deployment_of_the_checkout_is_healthy(self):
        lines, healthy = report(status(), DEPLOYED)
        self.assertTrue(healthy)
        self.assertEqual(
            lines,
            [
                '  Raicho             ready, version 0.1.0',
                '  Database           ready, sqlite 3.51.3',
                '  Connector          connected, 12 heartbeats',
                '  Deployed commit    f9b7238, matches the checkout',
                '  Health             healthy',
            ],
        )

    def test_a_disconnected_connector_is_unhealthy_and_names_its_error(self):
        lines, healthy = report(status(connector='disconnected', last_error='disconnected', heartbeats=0), DEPLOYED)
        self.assertFalse(healthy)
        self.assertIn('  Connector          disconnected, last error disconnected, 0 heartbeats', lines)
        self.assertEqual(lines[-1], '  Health             not healthy')

    def test_an_unavailable_application_is_unhealthy(self):
        self.assertFalse(report(status(application='unavailable'), DEPLOYED)[1])

    def test_an_older_deployment_counts_the_commits_behind(self):
        lines = report(status(), CHECKOUT, behind=10)[0]
        self.assertIn('  Deployed commit    f9b7238, 10 commits behind checkout 41dad85', lines)
        lines = report(status(), f'{CHECKOUT}-dirty')[0]
        self.assertIn('  Deployed commit    f9b7238, checkout is 41dad85-dirty', lines)

    def test_an_unknown_commit_is_reported(self):
        self.assertIn('  Deployed commit    unknown', report(status(commit=None), CHECKOUT)[0])


class CommitsBehindTests(unittest.TestCase):
    def test_counts_checkout_commits_missing_from_the_deployment(self):
        with tempfile.TemporaryDirectory() as directory:

            def git(*arguments):
                return subprocess.run(
                    ['git', *arguments], cwd=directory, capture_output=True, text=True, check=True
                ).stdout.strip()

            git('init', '--quiet')
            commits = []
            for message in ('first', 'second', 'third'):
                git(*IDENTITY, 'commit', '--allow-empty', '-qm', message)
                commits.append(git('rev-parse', 'HEAD'))
            self.assertEqual(commits_behind(commits[0], commits[2], directory), 2)
            self.assertEqual(commits_behind(commits[0], f'{commits[2]}-dirty', directory), 2)
            self.assertIsNone(commits_behind('0' * 40, commits[2], directory))
            self.assertIsNone(commits_behind(commits[0], 'unknown', directory))


class DeploymentHealthCommandTests(unittest.TestCase):
    def run_health(self, text):
        return subprocess.run(
            [sys.executable, '-B', '-m', 'automation.tooling.deployment_health', DEPLOYED],
            cwd=REPOSITORY_ROOT,
            env=os.environ | {'PYTHONPATH': str(REPOSITORY_ROOT)},
            input=text,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_a_healthy_response_prints_the_report(self):
        result = self.run_health(json.dumps(status()))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.endswith('  Health             healthy\n'))

    def test_no_response_fails_with_a_hint(self):
        result = self.run_health('')
        self.assertEqual(result.returncode, 1)
        self.assertIn('make deploy-ps', result.stderr)

    def test_an_unreadable_response_fails(self):
        result = self.run_health('<html>')
        self.assertEqual(result.returncode, 1)
        self.assertIn('unexpected status response', result.stderr)


if __name__ == '__main__':
    unittest.main()
