import json
import os
import re
import shutil
import subprocess
import sys

from raicho_changelog import parse_description_entries

SUBJECT_NUMBER = re.compile(r'\(#(\d+)\)\s*$')
MERGE_NUMBER = re.compile(r'^Merge pull request #(\d+) ')


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
    result = subprocess.run(
        ['gh', 'api', f'repos/{repository}/pulls/{number}', '--include'],
        check=False,
        capture_output=True,
        text=True,
    )
    headers, separator, payload = result.stdout.partition('\n\n')
    if result.returncode != 0:
        if re.match(r'^HTTP/[\d.]+ 404(?:\s|$)', headers):
            print(f'#{number} is not a pull request. Skipping it.', file=sys.stderr)
            return None
        raise ValueError(
            f'Cannot read pull request #{number} in {repository}: '
            f'{result.stderr.strip() or headers}'
        )
    if not separator:
        raise ValueError(f'Cannot read pull request #{number}: missing HTTP response')
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ValueError(f'Cannot read pull request #{number}: invalid JSON') from error
    if not isinstance(data, dict) or 'body' not in data:
        raise ValueError(f'Pull request #{number} is missing its body')
    body = data['body']
    labels = data.get('labels')
    if body is not None and not isinstance(body, str):
        raise ValueError(f'Pull request #{number} has an invalid body')
    if not isinstance(labels, list) or any(
        not isinstance(label, dict) or not isinstance(label.get('name'), str)
        for label in labels
    ):
        raise ValueError(f'Pull request #{number} has invalid or missing labels')
    return body or '', [label['name'] for label in labels]


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
