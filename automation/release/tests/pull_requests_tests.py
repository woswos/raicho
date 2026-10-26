import json
import os
import subprocess
import unittest
from unittest.mock import patch

from automation.release.pull_requests import github_pull_request


def response(status=200, payload=None, error=''):
    body = json.dumps(payload)
    return subprocess.CompletedProcess(
        ['gh'],
        0 if status == 200 else 1,
        f'HTTP/2.0 {status}\nContent-Type: application/json\n\n{body}',
        error,
    )


class ReleaseRequestTests(unittest.TestCase):
    def request(self, result):
        with (
            patch.dict(os.environ, {'GITHUB_REPOSITORY': 'example/raicho'}),
            patch(
                'automation.release.pull_requests.subprocess.run',
                return_value=result,
            ) as run,
        ):
            found = github_pull_request('12')
        self.assertEqual(run.call_count, 1)
        return found

    def test_reads_body_and_labels_from_one_response(self):
        result = response(
            payload={
                'body': '## Changelog\n\n### Fixed\n\n- Corrected.',
                'labels': [{'name': 'skip changelog'}],
            }
        )
        body, labels = self.request(result)
        self.assertIn('- Corrected.', body)
        self.assertEqual(labels, ['skip changelog'])

    def test_null_body_is_empty(self):
        self.assertEqual(
            self.request(response(payload={'body': None, 'labels': []})), ('', [])
        )

    def test_nonexistent_pull_request_is_skipped(self):
        self.assertIsNone(self.request(response(404, {'message': 'Not Found'})))

    def test_api_errors_abort_instead_of_losing_entries(self):
        for status in (401, 403, 429, 500):
            with (
                self.subTest(status=status),
                self.assertRaisesRegex(ValueError, r'pull request #12.*HTTP'),
            ):
                self.request(response(status, {}, f'HTTP {status}'))

    def test_transport_error_aborts(self):
        result = subprocess.CompletedProcess(['gh'], 1, '', 'connection failed')
        with self.assertRaisesRegex(ValueError, 'connection failed'):
            self.request(result)

    def test_incomplete_or_invalid_metadata_aborts(self):
        for payload in (
            {},
            {'body': 'note'},
            {'body': 42, 'labels': []},
            {'body': '', 'labels': None},
            {'body': '', 'labels': [{}]},
            {'body': '', 'labels': [{'name': None}]},
            [],
        ):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                self.request(response(payload=payload))

    def test_invalid_json_aborts(self):
        result = subprocess.CompletedProcess(['gh'], 0, 'HTTP/2.0 200\n\n{', '')
        with self.assertRaises(ValueError):
            self.request(result)
