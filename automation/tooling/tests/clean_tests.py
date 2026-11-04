import unittest

from automation.testing.docker_mock import Response
from automation.tooling.tests.cleanup_fixture import PROJECT_FILTER, PROJECT_FORMAT, CleanupFixture


class CleanTests(CleanupFixture):
    def clean(self, *responses):
        return self.run_script('clean.bash', *responses)

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
        commands, result = self.clean(
            Response(
                ('container', 'ls', '--format', PROJECT_FORMAT),
                output='raicho\nraicho-runtime-20261026120000-123\n\n',
            ),
            Response(
                ('volume', 'ls', '--format', PROJECT_FORMAT),
                output='raicho\nraicho-mail-test\nraicho-connector-20261026120000-4\n'
                'raicho-connector-browsing-20261026120000-5\nraicho-tools-local\n',
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
                (
                    'volume',
                    '--quiet',
                    f'{PROJECT_FILTER}raicho-connector-browsing-20261026120000-5',
                ),
                output='browsing-volume\n',
            ),
            Response(
                ('network', '--quiet', f'{PROJECT_FILTER}raicho-ci-123-1'),
                output='ci-network\n',
            ),
            Response(('container', 'inspect', 'runtime-container'), output='false runtime-container\n'),
        )
        self.assertIn(['container', 'stop', 'runtime-container'], commands)
        self.assertIn(['container', 'rm', 'runtime-container'], commands)
        self.assertIn(['volume', 'rm', 'connector-volume'], commands)
        self.assertIn(['volume', 'rm', 'browsing-volume'], commands)
        self.assertIn(['network', 'rm', 'ci-network'], commands)
        self.assertEqual(
            sorted(line for line in result.stdout.splitlines() if line.startswith('Removed the ')),
            [
                'Removed the containers of raicho-runtime-20261026120000-123',
                'Removed the networks of raicho-ci-123-1',
                'Removed the volumes of raicho-connector-20261026120000-4',
                'Removed the volumes of raicho-connector-browsing-20261026120000-5',
            ],
        )

    def test_a_failed_docker_listing_fails_the_clean(self):
        for words in (('volume', 'ls', '--format'), ('image', 'ls')):
            with self.subTest(words=words):
                _, result = self.run_script('clean.bash', Response(words, status=1), status=1)
                self.assertNotIn('Clean finished', result.stdout)

    def test_removes_only_disposable_images(self):
        commands, result = self.clean(
            Response(
                ('image', 'ls', '--format'),
                output='raicho-mail-20261026120000-5:tools\nraicho-server:local\nother:latest\n',
            ),
        )
        removed = [command[2] for command in commands if command[:2] == ['image', 'rm']]
        self.assertEqual(removed, ['raicho-mail-20261026120000-5:tools'])
        self.assertIn('Project images', result.stdout)

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
