import subprocess
import tempfile
import unittest

from automation.raicho_paths import REPOSITORY_ROOT
from automation.testing.raicho_docker_mock import DockerMock, Response


class RunnerCleanupTests(unittest.TestCase):
    def test_ci_termination_removes_the_owned_project_and_image_tags(self):
        for name, prefix, tags in (
            ('mail_compatibility', 'raicho-mail-', ('thunderbird', 'tools')),
        ):
            with self.subTest(runner=name):
                commands = [
                    ' '.join(command) for command in self.interrupt_runner(name)
                ]
                self.assertTrue(
                    any('down --volumes --remove-orphans' in line for line in commands)
                )
                removal = next(
                    line for line in commands if line.startswith('image rm ')
                )
                images = removal.split()[2:]
                self.assertEqual(len(images), len(tags))
                self.assertTrue(all(image.startswith(prefix) for image in images))
                self.assertEqual(
                    {image.rsplit(':', 1)[1] for image in images}, set(tags)
                )

    def interrupt_runner(self, name):
        runner = (
            REPOSITORY_ROOT / 'extension/mailprobe/tests' / f'raicho_check_{name}.bash'
        )
        with tempfile.TemporaryDirectory() as temporary:
            docker = DockerMock(
                temporary, [Response(('build',), terminate_parent=True)]
            )
            result = subprocess.run(
                ['bash', str(runner)],
                env=docker.environment(),
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            commands = docker.commands()
        self.assertNotEqual(result.returncode, 0)
        return commands
