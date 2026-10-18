"""Turn the changelog and merged pull requests into the next product version.

This reads git and, when the environment allows, pull request descriptions.
It does not commit, tag, or push. Pass --write to date CHANGELOG.md and store
the new version in Cargo.toml and any extension manifests.

    python3 -B devbin/raicho_cut_release.py
    python3 -B devbin/raicho_cut_release.py --write
    python3 -B devbin/raicho_cut_release.py --write --major
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from raicho_changelog import (
    date_changelog,
    next_version,
    parse_description_entries,
    release_section,
    requests_minor,
    unreleased_body,
)
from raicho_version import parse_version, write_product_version

SUBJECT_NUMBER = re.compile(r'\(#(\d+)\)\s*$')
MERGE_NUMBER = re.compile(r'^Merge pull request #(\d+) ')


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


def numbers_in_subject(subject):
    numbers = []
    match = SUBJECT_NUMBER.search(subject)
    if match:
        numbers.append(match.group(1))
    match = MERGE_NUMBER.match(subject)
    if match:
        numbers.append(match.group(1))
    return numbers


def pull_request_numbers(root, latest):
    span = 'HEAD' if latest is None else f'v{latest}..HEAD'
    output = subprocess.check_output(
        ['git', 'log', '--reverse', '--format=%s', span],
        cwd=root,
        stderr=subprocess.PIPE,
        text=True,
    )
    numbers = []
    seen = set()
    for subject in output.splitlines():
        for number in numbers_in_subject(subject):
            if number not in seen:
                seen.add(number)
                numbers.append(number)
    return numbers


def fetch_blocker():
    if not os.environ.get('GITHUB_REPOSITORY'):
        return (
            'Not reading pull request descriptions: no GITHUB_REPOSITORY '
            'in the environment.'
        )
    if not (os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')):
        return (
            'Not reading pull request descriptions: no GH_TOKEN or GITHUB_TOKEN. '
            'A workflow step needs one passed to it explicitly.'
        )
    if shutil.which('gh') is None:
        return 'Not reading pull request descriptions: gh is not installed.'
    return None


def github_pull_request(number):
    repository = os.environ['GITHUB_REPOSITORY']
    body = subprocess.run(
        [
            'gh',
            'api',
            f'repos/{repository}/pulls/{number}',
            '--jq',
            '.body // ""',
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if body.returncode != 0:
        print(f'Cannot read pull request #{number}. Skipping it.', file=sys.stderr)
        return None
    labels = subprocess.run(
        [
            'gh',
            'api',
            f'repos/{repository}/pulls/{number}',
            '--jq',
            '.labels[].name',
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    names = labels.stdout.splitlines() if labels.returncode == 0 else []
    return body.stdout, names


def collect_entries(root, latest):
    blocker = fetch_blocker()
    if blocker:
        print(blocker, file=sys.stderr)
        return {}, 0
    parsed = {}
    count = 0
    for number in pull_request_numbers(root, latest):
        result = github_pull_request(number)
        if result is None:
            continue
        body, labels = result
        count += 1
        if 'no changelog' in labels:
            print(f'#{number} is labeled no changelog. Skipping it.', file=sys.stderr)
            continue
        for kind, items in parse_description_entries(body, number).items():
            parsed.setdefault(kind, []).extend(items)
    return parsed, count


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
        root = Path(__file__).resolve().parents[1]
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
