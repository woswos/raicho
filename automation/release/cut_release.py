"""Turn the changelog and merged pull requests into the next product version.

This reads git and, when the environment allows, pull request descriptions.
It does not commit, tag, or push. Pass --write to date CHANGELOG.md and store
the new version in Cargo.toml, Cargo.lock, and any extension manifests.

    python3 -B -m automation.release.cut_release
    python3 -B -m automation.release.cut_release --write
    python3 -B -m automation.release.cut_release --write --major
"""

import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from automation.paths import REPOSITORY_ROOT
from automation.release.changelog import (
    date_changelog,
    next_version,
    release_section,
    requests_minor,
    unreleased_body,
)
from automation.release.pull_requests import collect_entries
from automation.release.version import parse_version, write_product_version


def latest_release(root):
    output = subprocess.check_output(
        ['git', 'tag', '--list', 'v*'],
        cwd=root,
        stderr=subprocess.PIPE,
        text=True,
    )
    found = []
    for line in output.splitlines():
        if not line.startswith('v'):
            continue
        try:
            found.append((parse_version(line[1:]), line[1:]))
        except ValueError:
            continue
    if not found:
        return None
    return max(found)[1]


def report(released, version=''):
    path = os.environ.get('GITHUB_OUTPUT')
    if not path:
        return
    tag = f'v{version}' if version else ''
    with open(path, 'a', encoding='utf-8') as handle:
        handle.write(f'released={str(released).lower()}\n')
        handle.write(f'version={version}\n')
        handle.write(f'tag={tag}\n')


def parse_args(argv):
    write = False
    major = False
    root = None
    for argument in argv:
        if argument == '--write':
            write = True
        elif argument == '--major':
            major = True
        elif argument.startswith('-'):
            raise ValueError(f'unknown argument: {argument}')
        elif root is None:
            root = Path(argument)
        else:
            raise ValueError('expected at most one repository root')
    if root is None:
        root = REPOSITORY_ROOT
    return write, major, root.resolve()


def main(argv=None):
    try:
        write, major, root = parse_args(sys.argv[1:] if argv is None else argv)
        changelog_path = root / 'CHANGELOG.md'
        original = changelog_path.read_text()
        written = unreleased_body(original)
        latest = latest_release(root)
        parsed, count = collect_entries(root, latest)
        section = release_section(written, parsed)
        if not section.strip():
            previous = latest or 'the beginning'
            print(
                'Nothing under [Unreleased] and nothing in the pull requests '
                f'merged since {previous}, so there is nothing to release.'
            )
            report(False)
            return 0
        version, reason = next_version(latest, requests_minor(written, parsed), major)
        print(
            f'Next version: {version} ({reason}. The last tag was '
            f'{latest or "none"}, and {count} pull request(s) were read.)'
        )
        report(True, version)
        if not write:
            print('Nothing was written. Pass --write to date the changelog.')
            return 0
        today = datetime.now(UTC).date().isoformat()
        updated = date_changelog(original, version, today, section)
        write_product_version(root, version)
        changelog_path.write_text(updated)
        print(f'Wrote CHANGELOG.md: the entries are now under {version}.')
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
