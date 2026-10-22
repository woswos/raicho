"""Keep owned directory names consistent without changing reserved tool paths."""

import re
import subprocess
import sys
from pathlib import Path

from raicho_check_skills import SKILL_NAME
from raicho_check_source_naming import EXCLUDED, repository_paths

RESERVED_PATHS = {
    Path('.agents'),
    Path('.github'),
    Path('.github/PULL_REQUEST_TEMPLATE'),
}
SKILL_DIRECTORY = Path('.agents/skills')


def naming_rule(directory):
    if directory.parent == SKILL_DIRECTORY:
        return SKILL_NAME, 'lowercase kebab-case'
    return r'[a-z0-9]+', 'lowercase letters and digits only'


def check_directory_naming(root):
    root = Path(root).resolve()
    try:
        paths = repository_paths(root)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        return [f'cannot inspect Git repository {root}: {error}']
    directories = {
        directory
        for path in paths
        for directory in path.parents
        if directory != Path('.')
        and not EXCLUDED.intersection(directory.parts)
        and not directory.is_relative_to('assets/brand/references')
    }
    failures = []
    for directory in sorted(directories - RESERVED_PATHS):
        pattern, description = naming_rule(directory)
        if not re.fullmatch(pattern, directory.name):
            failures.append(f'{directory.as_posix()} must use {description}')
    return failures


def main():
    if len(sys.argv) > 2:
        print('FAIL: expected at most one repository root argument', file=sys.stderr)
        return 1
    root = (
        Path(sys.argv[1]).resolve()
        if len(sys.argv) == 2
        else Path(__file__).resolve().parents[1]
    )
    failures = check_directory_naming(root)
    for failure in failures:
        print(f'FAIL: {failure}', file=sys.stderr)
    if failures:
        return 1
    print('directory-naming check passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
