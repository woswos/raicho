import subprocess
import tempfile
import unittest
from pathlib import Path

from protocol.generator.cli import NODE_REPORTER

PASSING = """import assert from 'node:assert/strict';
import { test } from 'node:test';
test('adds', () => assert.equal(1 + 1, 2));
test('skips', { skip: true }, () => {});
"""
FAILING = """import assert from 'node:assert/strict';
import { test } from 'node:test';
test('compares', () => assert.equal('actual', 'expected'));
"""


class NodeReporterTests(unittest.TestCase):
    def run_tests(self, source):
        with tempfile.TemporaryDirectory(prefix='raicho-node-reporter-') as directory:
            test = Path(directory) / 'example.test.mjs'
            test.write_text(source)
            return subprocess.run(
                ['node', '--test', NODE_REPORTER, str(test)],
                cwd=directory,
                capture_output=True,
                text=True,
                check=False,
            )

    def test_passing_suite_prints_one_summary_line(self):
        result = self.run_tests(PASSING)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, 'Node: 1 tests passed, 1 skipped in .\n')

    def test_failure_prints_the_test_and_its_assertion(self):
        result = self.run_tests(FAILING)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('✖ compares (example.test.mjs:3', result.stdout)
        self.assertIn("'expected'", result.stdout)
        self.assertIn('Node: 1 failed, 0 passed', result.stdout)


if __name__ == '__main__':
    unittest.main()
