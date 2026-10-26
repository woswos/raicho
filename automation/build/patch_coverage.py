import subprocess
import sys

from automation.build.coverage_report import OUTPUT
from automation.paths import REPOSITORY_ROOT
from automation.repository.pr_context import git_output, load_context

MINIMUM_PERCENT = 90


def comparison_base(root):
    base = load_context(root)['base']
    if base is not None:
        return base
    try:
        return (
            git_output('merge-base', 'HEAD', 'origin/main', root=root).decode().strip()
        )
    except subprocess.CalledProcessError:
        raise ValueError(
            'No comparison base: set PR_BASE_SHA or fetch origin/main.'
        ) from None


def main():
    try:
        base = comparison_base(REPOSITORY_ROOT)
    except ValueError as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    reports = sorted(OUTPUT.glob('*.info'))
    if not reports:
        print('FAIL: No coverage reports. Run make coverage first.', file=sys.stderr)
        return 1
    return subprocess.run(
        [
            'diff-cover',
            *map(str, reports),
            f'--compare-branch={base}',
            f'--fail-under={MINIMUM_PERCENT}',
            '--show-uncovered',
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
    ).returncode


if __name__ == '__main__':
    sys.exit(main())
