"""Print one changelog section for use as release notes."""

import sys

from automation.raicho_paths import REPOSITORY_ROOT
from automation.release.raicho_changelog import release_notes
from automation.release.raicho_version import parse_version


def main():
    if len(sys.argv) != 2:
        print('usage: raicho_release_notes.py VERSION', file=sys.stderr)
        return 1
    root = REPOSITORY_ROOT
    try:
        version = sys.argv[1].removeprefix('v')
        parse_version(version)
        sys.stdout.write(release_notes((root / 'CHANGELOG.md').read_text(), version))
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
