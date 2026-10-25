import os
import subprocess
import sys

from automation.raicho_paths import REPOSITORY_ROOT


def run_builder(*arguments, source_root=REPOSITORY_ROOT, cwd=None):
    return subprocess.run(
        [sys.executable, '-B', '-m', 'extension.raicho_build_extension', *arguments],
        cwd=cwd,
        env=os.environ | {'PYTHONPATH': str(source_root)},
        capture_output=True,
        text=True,
        check=False,
    )
