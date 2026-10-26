import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from automation.paths import REPOSITORY_ROOT

CANONICAL_NAMES = {'README.md', 'CHANGELOG.md', 'AGENTS.md', 'LICENSE.md'}
KEBAB_NAME = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\.md')
DATED_NAME = re.compile(r'\d{8}-[a-z0-9]+(?:-[a-z0-9]+)*\.md')


def valid_date(filename):
    try:
        datetime.strptime(filename[:8], '%Y%m%d')
    except ValueError:
        return False
    return True


def plan_failure(name, parts):
    if len(parts) == 3 and parts[2] == 'template.md':
        return None
    if len(parts) == 4 and parts[2] in {'active', 'done'}:
        leaf = parts[3]
        if leaf == 'template.md':
            return None
        if DATED_NAME.fullmatch(leaf):
            if valid_date(leaf):
                return None
            return f'invalid date prefix: {name}'
    return f'planning document must be template.md or a dated file in active/ or done/: {name}'


def decision_failure(name, parts):
    if len(parts) == 3:
        leaf = parts[2]
        if leaf == 'template.md':
            return None
        if DATED_NAME.fullmatch(leaf):
            if valid_date(leaf):
                return None
            return f'invalid date prefix: {name}'
    return f'decision record must be template.md or a dated file in docs/decisions/: {name}'


def filename_failure(name):
    path = Path(name)
    if path.name in CANONICAL_NAMES:
        return None
    if not KEBAB_NAME.fullmatch(path.name):
        return f'invalid documentation filename: {name}'
    parts = path.parts
    if len(parts) > 1 and parts[0] == 'docs' and parts[1] == 'planning':
        return plan_failure(name, parts)
    if len(parts) > 1 and parts[0] == 'docs' and parts[1] == 'decisions':
        return decision_failure(name, parts)
    return None


def check_doc_naming(root):
    root = Path(root)
    failures = []
    try:
        output = subprocess.check_output(
            [
                'git',
                'ls-files',
                '-z',
                '--cached',
                '--others',
                '--exclude-standard',
                '--',
                'docs',
            ],
            cwd=root,
            stderr=subprocess.PIPE,
        )
        names = output.decode().split('\0')
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        return [str(error)]
    for name in sorted(set(names)):
        if not name or not name.endswith('.md'):
            continue
        disk = root / name
        if disk.is_symlink() or (disk.exists() and not disk.is_file()):
            failures.append(f'documentation must be a regular file: {name}')
            continue
        failure = filename_failure(name)
        if failure:
            failures.append(failure)
    return failures


def main():
    if len(sys.argv) > 2:
        print('FAIL: expected at most one repository root argument', file=sys.stderr)
        return 1
    root = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else REPOSITORY_ROOT
    failures = check_doc_naming(root)
    for failure in failures:
        print(f'FAIL: {failure}', file=sys.stderr)
    if failures:
        return 1
    print('doc-naming check passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
