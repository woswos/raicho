import os
import subprocess
import tempfile
import unittest

from automation.paths import REPOSITORY_ROOT


class HostMakeTests(unittest.TestCase):
    def test_a_relative_cache_directory_resolves_from_the_callers_directory(self):
        host = {name: value for name, value in os.environ.items() if name != 'RAICHO_TOOLING_CONTAINER'}
        with tempfile.TemporaryDirectory() as directory:
            cache = subprocess.run(
                [
                    'make',
                    '--no-print-directory',
                    '-f',
                    str(REPOSITORY_ROOT / 'Makefile'),
                    '--eval',
                    'print-cache: ; @printf "%s" "$$RAICHO_CACHE_DIRECTORY"',
                    'print-cache',
                ],
                cwd=directory,
                env=host | {'RAICHO_CACHE_DIRECTORY': 'cache'},
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            self.assertEqual(cache, os.path.join(os.path.realpath(directory), 'cache'))


if __name__ == '__main__':
    unittest.main()
