import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from automation.paths import REPOSITORY_ROOT
from automation.tooling.deployment_health import commit_distance, report

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

    def test_a_different_deployment_names_its_position(self):
        cases = (
            ((0, 10), 'f9b7238, 10 commits behind checkout 41dad85'),
            ((3, 0), 'f9b7238, 3 commits ahead of checkout 41dad85'),
            ((2, 5), 'f9b7238, diverged from checkout 41dad85: 2 ahead, 5 behind'),
            (None, 'f9b7238, checkout is 41dad85'),
        )
        for distance, line in cases:
            with self.subTest(distance=distance):
                self.assertIn(f'  Deployed commit    {line}', report(status(), CHECKOUT, distance)[0])
        lines = report(status(), f'{CHECKOUT}-dirty')[0]
        self.assertIn('  Deployed commit    f9b7238, checkout is 41dad85-dirty', lines)

    def test_an_unknown_commit_is_reported(self):
        self.assertIn('  Deployed commit    unknown', report(status(commit=None), CHECKOUT)[0])


class CommitDistanceTests(unittest.TestCase):
    def test_counts_the_commits_on_each_side(self):
        with tempfile.TemporaryDirectory() as directory:

            def git(*arguments):
                return subprocess.run(
                    ['git', *arguments], cwd=directory, capture_output=True, text=True, check=True
                ).stdout.strip()

            def commit(message):
                git(*IDENTITY, 'commit', '--allow-empty', '-qm', message)
                return git('rev-parse', 'HEAD')

            git('init', '--quiet')
            first, _, third = (commit(message) for message in ('first', 'second', 'third'))
            git('checkout', '--quiet', '-b', 'side', first)
            side = commit('side')
            self.assertEqual(commit_distance(first, third, directory), (0, 2))
            self.assertEqual(commit_distance(third, first, directory), (2, 0))
            self.assertEqual(commit_distance(side, f'{third}-dirty', directory), (1, 2))
            self.assertIsNone(commit_distance('0' * 40, third, directory))

    def test_only_full_commit_hashes_reach_git(self):
        for deployed in ('unknown', '--output=/tmp/x', 'f9b7238'):
            with self.subTest(deployed=deployed), mock.patch.object(subprocess, 'run') as run:
                self.assertIsNone(commit_distance(deployed, CHECKOUT))
                run.assert_not_called()


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
