import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from raicho_pr_context import description_references, load_context, regular_file_at


def reference_failure(kind, path):
    directory = (
        r'docs/planning/(?:active|done)' if kind == 'Design' else r'docs/decisions'
    )
    if not re.fullmatch(directory + r'/\d{8}-[a-z0-9]+(?:-[a-z0-9]+)*\.md', path):
        return f'invalid {kind} document path: {path}'
    try:
        datetime.strptime(Path(path).name[:8], '%Y%m%d')
    except ValueError:
        return f'invalid date prefix: {path}'
    return None


def check_design_reference(context, root):
    references = description_references(context['description'])
    if len(references) != 1:
        raise ValueError(
            'description needs exactly one standalone Design: or Decision: path'
        )
    kind, path = references[0]
    failure = reference_failure(kind, path)
    if failure:
        raise ValueError(failure)
    commit = context['base'] if kind == 'Design' else context['head']
    if commit is None:
        raise ValueError('Design lookup requires PR_BASE_SHA in local runs')
    if not regular_file_at(commit, path, root):
        location = (
            'target commit (merge the design first)'
            if kind == 'Design'
            else 'PR head commit'
        )
        raise ValueError(
            f'{kind} document is not a regular file at the {location}: {path}'
        )
    return path


def main():
    if len(sys.argv) > 2:
        print('FAIL: expected at most one repository root argument', file=sys.stderr)
        return 1
    root = (
        Path(sys.argv[1]).resolve()
        if len(sys.argv) == 2
        else Path(__file__).resolve().parents[1]
    )
    try:
        path = check_design_reference(load_context(root), root)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    print(f'design-link check passed: {path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
