import subprocess
import tempfile
import unittest

from automation.paths import REPOSITORY_ROOT
from automation.testing.docker_mock import DockerMock, Response


class RunnerCleanupTests(unittest.TestCase):
    def test_ci_termination_removes_the_owned_project_and_image_tags(self):
        commands = [' '.join(command) for command in self.interrupt_runner()]
        evidence_index = next(index for index, line in enumerate(commands) if line.endswith('run --rm driver evidence'))
        logs_index = next(index for index, line in enumerate(commands) if ' logs --timestamps ' in line)
        thunderbird_log_index = next(
            index for index, line in enumerate(commands) if line.endswith('mailprobe.tests.profile.moz_log')
        )
        teardown_index = next(index for index, line in enumerate(commands) if 'down --volumes --remove-orphans' in line)
        self.assertLess(max(evidence_index, logs_index, thunderbird_log_index), teardown_index)
        removal = next(line for line in commands if line.startswith('image rm '))
        images = removal.split()[2:]
        self.assertEqual(len(images), 2)
        self.assertTrue(all(image.startswith('raicho-mail-') for image in images))
        self.assertEqual({image.rsplit(':', 1)[1] for image in images}, {'thunderbird', 'tools'})

    def interrupt_runner(self):
        runner = REPOSITORY_ROOT / 'mailprobe/tests/check_mail_compatibility.bash'
        with tempfile.TemporaryDirectory() as temporary:
            docker = DockerMock(temporary, [Response(('build',), terminate_parent=True)])
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
