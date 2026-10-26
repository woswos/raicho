import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from automation.paths import REPOSITORY_ROOT
from automation.testing.docker_mock import DockerMock

PROJECT_FORMAT = '{{.Label "com.docker.compose.project"}}'
PROJECT_FILTER = 'label=com.docker.compose.project='
SCRIPTS = ('clean.bash', 'mrproper.bash', 'deploy_clean.bash')


class CleanupFixture(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-clean-test-')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.root = self.directory / 'repository'
        tooling = self.root / 'automation/tooling'
        tooling.mkdir(parents=True)
        for script in SCRIPTS:
            shutil.copyfile(REPOSITORY_ROOT / 'automation/tooling' / script, tooling / script)
        shutil.copyfile(REPOSITORY_ROOT / '.gitignore', self.root / '.gitignore')
        subprocess.run(['git', 'init', '-q'], cwd=self.root, check=True)
        self.temporary = self.directory / 'tmp'
        self.temporary.mkdir()

    def write(self, relative, text=''):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def run_script(self, script, *responses, answer='', status=0, **environment):
        docker = DockerMock(self.directory / 'commands', responses)
        result = subprocess.run(
            ['bash', str(self.root / 'automation/tooling' / script)],
            env=docker.environment(TMPDIR=str(self.temporary), **environment),
            input=answer,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, status, result.stderr)
        return docker.commands(), result
