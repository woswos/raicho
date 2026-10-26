import subprocess
import tempfile
import unittest
from pathlib import Path

from automation.paths import REPOSITORY_ROOT
from automation.testing.docker_mock import DockerMock

SCRIPT = REPOSITORY_ROOT / 'automation/tooling/cache_images.bash'


class CacheImagesTests(unittest.TestCase):
    def build(self, *images, status=0, **environment):
        with tempfile.TemporaryDirectory() as directory:
            docker = DockerMock(Path(directory))
            variables = {'ACTIONS_RUNTIME_TOKEN': '', 'RAICHO_IMAGE_CACHE_WRITE': '', 'RAICHO_COMMIT': 'abc'}
            result = subprocess.run(
                ['bash', str(SCRIPT), *images],
                env=docker.environment(**(variables | environment)),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, status, result.stderr)
            return docker.commands(), result

    def test_images_match_their_compose_builds(self):
        commands, _ = self.build('gateway', 'server')
        self.assertEqual(
            commands,
            [
                [
                    'buildx',
                    'build',
                    '--load',
                    '--progress',
                    'quiet',
                    '--file',
                    'deploy/gateway/Dockerfile',
                    '--tag',
                    'raicho-gateway:local',
                    '.',
                ],
                [
                    'buildx',
                    'build',
                    '--load',
                    '--progress',
                    'quiet',
                    '--file',
                    'deploy/raicho/Dockerfile',
                    '--tag',
                    'raicho-server:local',
                    '--build-arg',
                    'RAICHO_COMMIT=abc',
                    '.',
                ],
            ],
        )

    def test_the_actions_cache_is_read_and_written_only_when_asked(self):
        commands, _ = self.build('gateway', ACTIONS_RUNTIME_TOKEN='token')
        self.assertIn('type=gha,scope=gateway', commands[0])
        self.assertNotIn('--cache-to', commands[0])
        commands, _ = self.build('gateway', ACTIONS_RUNTIME_TOKEN='token', RAICHO_IMAGE_CACHE_WRITE='1')
        self.assertIn('type=gha,scope=gateway,mode=max', commands[0])

    def test_unknown_images_fail(self):
        # The tooling image builds about as fast as it loads from the cache.
        for image in ('database', 'tools'):
            with self.subTest(image=image):
                commands, result = self.build(image, status=1)
                self.assertEqual(commands, [])
                self.assertIn(f'FAIL: unknown image {image}', result.stderr)


if __name__ == '__main__':
    unittest.main()
