import subprocess

from automation.paths import REPOSITORY_ROOT


def run_builder(*arguments, source_root=REPOSITORY_ROOT, cwd=None):
    return subprocess.run(
        ['node', str(source_root / 'extension/build.mjs'), *arguments],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
