import os
import subprocess
import tempfile
import unittest
from pathlib import Path

RUNNER = Path(__file__).with_name('raicho_check_extension_lifecycle.bash')


class RunnerCleanupTests(unittest.TestCase):
    def test_ci_termination_removes_the_owned_project_and_image_tags(self):
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
                ['bash', str(RUNNER)],
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
        self.assertIn('down --volumes --remove-orphans', commands)
        self.assertIn('image rm raicho-lifecycle-', commands)
