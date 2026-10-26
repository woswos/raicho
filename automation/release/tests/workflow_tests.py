import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

WORKFLOWS = Path(__file__).resolve().parents[1] / '.github/workflows'


def interpolate(text, context):
    return re.sub(
        r'\$\{\{\s*([^{}]+?)\s*\}\}',
        lambda match: context[match.group(1).strip()],
        text,
    )


class ReleaseWorkflowTests(unittest.TestCase):
    def confirmation_step(self):
        workflow = yaml.safe_load((WORKFLOWS / 'major-release.yml').read_text())
        return next(
            step
            for step in workflow['jobs']['cut']['steps']
            if step.get('name') == 'Check the confirmation and the token'
        )

    def run_confirmation(self, root, confirmation, token='configured'):
        step = self.confirmation_step()
        context = {'inputs.confirm': confirmation, 'secrets.RELEASE_TOKEN': token}
        environment = {'PATH': '/usr/bin:/bin'}
        environment.update(
            {
                name: interpolate(value, context)
                for name, value in step.get('env', {}).items()
            }
        )
        return subprocess.run(
            [
                'bash',
                '--noprofile',
                '--norc',
                '-e',
                '-o',
                'pipefail',
                '-c',
                interpolate(step['run'], context),
            ],
            cwd=root,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_explicit_confirmation_with_token_succeeds(self):
        with tempfile.TemporaryDirectory(prefix='raicho-release-workflow-') as root:
            result = self.run_confirmation(root, 'MAJOR')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_confirmation_requires_exact_text(self):
        with tempfile.TemporaryDirectory(prefix='raicho-release-workflow-') as root:
            for confirmation in ('', 'major', 'MAJOR ', ' MAJOR', 'MAJOR\n'):
                with self.subTest(confirmation=confirmation):
                    result = self.run_confirmation(root, confirmation)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('Type MAJOR to confirm', result.stdout)

    def test_confirmation_cannot_execute_shell_commands(self):
        with tempfile.TemporaryDirectory(prefix='raicho-release-workflow-') as root:
            result = self.run_confirmation(root, '$(touch injected)')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Type MAJOR to confirm', result.stdout)
            self.assertFalse((Path(root) / 'injected').exists())

    def test_missing_token_stops_the_release(self):
        with tempfile.TemporaryDirectory(prefix='raicho-release-workflow-') as root:
            result = self.run_confirmation(root, 'MAJOR', token='')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('No RELEASE_TOKEN is set', result.stdout)
