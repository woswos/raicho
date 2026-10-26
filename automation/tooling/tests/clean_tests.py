import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from automation.paths import REPOSITORY_ROOT
from automation.testing.docker_mock import DockerMock, Response

PROJECT_FORMAT = '{{.Label "com.docker.compose.project"}}'
PROJECT_FILTER = 'label=com.docker.compose.project='


class CleanTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-clean-test-')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.root = self.directory / 'repository'
        self.script = self.root / 'automation/tooling/clean.bash'
        self.script.parent.mkdir(parents=True)
        shutil.copyfile(REPOSITORY_ROOT / 'automation/tooling/clean.bash', self.script)
        shutil.copyfile(REPOSITORY_ROOT / '.gitignore', self.root / '.gitignore')
        subprocess.run(['git', 'init', '-q'], cwd=self.root, check=True)
        self.temporary = self.directory / 'tmp'
        self.temporary.mkdir()

    def write(self, relative, text=''):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def clean(self, *responses):
        docker = DockerMock(self.directory / 'commands', responses)
        result = subprocess.run(
            ['bash', str(self.script)],
            env=docker.environment(TMPDIR=str(self.temporary)),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return docker.commands(), result

    def test_removes_only_output_that_the_repository_ignores(self):
        removed = (
            'target/debug/raicho-server',
            'web/dist/main.js',
            'node_modules/package/index.js',
            'tool/__pycache__/module.cpython-313.pyc',
            'tool/stale.pyc',
        )
        for path in removed:
            self.write(path)
        kept = [
            self.write('.raicho/raicho/credentials/connector.token', 'secret\n'),
            self.write('notes.txt'),
            self.write('editor.local'),
        ]
        (self.root / '.git/info/exclude').write_text('editor.local\n')
        self.clean()
        for path in ('target', 'web/dist', 'node_modules', 'tool/__pycache__'):
            with self.subTest(path=path):
                self.assertFalse((self.root / path).exists())
        self.assertFalse((self.root / 'tool/stale.pyc').exists())
        for path in kept:
            with self.subTest(path=path):
                self.assertTrue(path.exists())

    def test_removes_only_disposable_acceptance_projects(self):
        commands, _ = self.clean(
            Response(
                ('container', 'ls', '--format', PROJECT_FORMAT),
                output='raicho\nraicho-runtime-20261026120000-123\n\n',
            ),
            Response(
                ('volume', 'ls', '--format', PROJECT_FORMAT),
                output='raicho\nraicho-mail-test\nraicho-connector-20261026120000-4\n',
            ),
            Response(
                ('network', 'ls', '--format', PROJECT_FORMAT),
                output='raicho-ci-123-1\n',
            ),
            Response(
                (
                    'container',
                    '--quiet',
                    f'{PROJECT_FILTER}raicho-runtime-20261026120000-123',
                ),
                output='runtime-container\n',
            ),
            Response(
                (
                    'volume',
                    '--quiet',
                    f'{PROJECT_FILTER}raicho-connector-20261026120000-4',
                ),
                output='connector-volume\n',
            ),
            Response(
                ('network', '--quiet', f'{PROJECT_FILTER}raicho-ci-123-1'),
                output='ci-network\n',
            ),
        )
        self.assertIn(['container', 'rm', '--force', 'runtime-container'], commands)
        self.assertIn(['volume', 'rm', 'connector-volume'], commands)
        self.assertIn(['network', 'rm', 'ci-network'], commands)
        filters = {word for command in commands for word in command if PROJECT_FILTER in word}
        self.assertEqual(
            {name.removeprefix(PROJECT_FILTER) for name in filters},
            {
                'raicho-runtime-20261026120000-123',
                'raicho-connector-20261026120000-4',
                'raicho-ci-123-1',
            },
        )

    def test_keeps_images_in_use_and_images_of_other_projects(self):
        commands, result = self.clean(
            Response(
                ('image', 'ls', '--format'),
                output='raicho-mail-20261026120000-5:tools\nraicho-server:local\nother:latest\n',
            ),
            Response(('image', 'rm', 'raicho-server:local'), status=1),
        )
        removed = [command[2] for command in commands if command[:2] == ['image', 'rm']]
        self.assertIn('raicho-mail-20261026120000-5:tools', removed)
        self.assertIn('raicho-tools:local', removed)
        self.assertNotIn('other:latest', removed)
        self.assertIn('Kept image raicho-server:local', result.stderr)

    def test_removes_the_tooling_cache_unless_a_container_uses_it(self):
        commands, _ = self.clean()
        self.assertIn(['volume', 'rm', 'raicho-tools_cache'], commands)
        _, result = self.clean(Response(('volume', 'rm', 'raicho-tools_cache'), status=1))
        self.assertIn('Kept cache volume raicho-tools_cache', result.stderr)

    def test_removes_acceptance_state_directories_only(self):
        state = self.temporary / 'raicho-credentials.Ab3dE5gH'
        (state / 'credentials').mkdir(parents=True)
        (state / 'credentials/connector.token').write_text('secret\n')
        others = [
            self.temporary / 'raicho-tooling-abc',
            self.temporary / 'raicho-x.short',
        ]
        for directory in others:
            directory.mkdir()
        self.clean()
        self.assertFalse(state.exists())
        for directory in others:
            with self.subTest(directory=directory):
                self.assertTrue(directory.exists())


if __name__ == '__main__':
    unittest.main()
