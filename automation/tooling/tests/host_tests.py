import os
import subprocess
import tempfile
import unittest

from automation.paths import REPOSITORY_ROOT
from automation.tooling.tests.deployment_tests import SELECTION, dry_run


class HostMakeTests(unittest.TestCase):
    def test_a_relative_cache_directory_resolves_from_the_callers_directory(self):
        host = {name: value for name, value in os.environ.items() if name not in SELECTION}
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

    def test_a_shell_opens_in_the_read_only_tooling_container(self):
        commands = dry_run('shell')
        self.assertRegex(commands, r'step\.bash tooling-image docker compose .* build\n')
        self.assertRegex(commands, r' run --rm(?: --volume \S+)? check bash\n$')


if __name__ == '__main__':
    unittest.main()
