import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from automation.raicho_paths import REPOSITORY_ROOT


class RunnerCleanupTests(unittest.TestCase):
    def test_ci_termination_removes_the_owned_project_and_image_tags(self):
        for name, prefix, tags in (
            (
                'extension_lifecycle',
                'raicho-lifecycle-',
                ('initial', 'upgrade', 'tools'),
            ),
            ('mail_compatibility', 'raicho-mail-', ('thunderbird', 'tools')),
        ):
            with self.subTest(runner=name):
                commands = self.interrupt_runner(name)
                self.assertIn('down --volumes --remove-orphans', commands)
                removal = next(
                    line
                    for line in commands.splitlines()
                    if line.startswith('image rm ')
                )
                images = removal.split()[2:]
                self.assertEqual(len(images), len(tags))
                self.assertTrue(all(image.startswith(prefix) for image in images))
                self.assertEqual(
                    {image.rsplit(':', 1)[1] for image in images}, set(tags)
                )

    def interrupt_runner(self, name):
        area = 'lifecycle' if name == 'extension_lifecycle' else 'mail'
        runner = (
            REPOSITORY_ROOT
            / 'automation/acceptance'
            / area
            / f'raicho_check_{name}.bash'
        )
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            docker = directory / 'docker'
            trace = directory / 'trace'
            docker.write_text(
                '#!/usr/bin/env bash\n'
                'printf "%s\\n" "${*}" >> "${MOCK_DOCKER_TRACE}"\n'
                'if [[ ${1} == build ]]; then kill -TERM "${PPID}"; fi\n'
                'exit 0\n'
            )
            docker.chmod(0o700)
            result = subprocess.run(
                ['bash', str(runner)],
                env={
                    **os.environ,
                    'PATH': f'{directory}:{os.environ["PATH"]}',
                    'MOCK_DOCKER_TRACE': str(trace),
                },
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            commands = trace.read_text()
        self.assertNotEqual(result.returncode, 0)
        return commands
