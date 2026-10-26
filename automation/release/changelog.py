"""Read Keep a Changelog sections and pull request changelog entries."""

import re

from automation.release.version import format_version, parse_version

KINDS = ('Added', 'Changed', 'Deprecated', 'Removed', 'Fixed', 'Security')
KIND_HEADING = re.compile(r'^### *(Added|Changed|Deprecated|Removed|Fixed|Security) *$')
MINOR_HEADING = re.compile(r'(?m)^### (?:Added|Removed)\s*$')


def section_body(text, marker):
    body = []
    collecting = False
    for line in text.splitlines():
        if line.startswith('## '):
            if collecting:
                break
            if marker in line:
                collecting = True
            continue
        if collecting:
            body.append(line)
    return '\n'.join(body).strip('\n')


def unreleased_body(text):
    return section_body(text, '[Unreleased]')


def release_notes(text, version):
    selected = version.removeprefix('v')
    parse_version(selected)
    notes = section_body(text, f'[{selected}]')
    if not notes:
        raise ValueError(f'no changelog section for {selected}')
    return notes + '\n'


def parse_description_entries(description, number=None):
    entries = {kind: [] for kind in KINDS}
    inside = False
    kind = ''
    entry = ''
    comment = False

    def flush():
        nonlocal entry
        text = entry.rstrip()
        if kind and text and not re.match(r'^[-*] *TODO:', text):
            suffix = f' (#{number})' if number else ''
            entries[kind].append(f'{text}{suffix}')
        entry = ''

    for line in description.splitlines():
        if '<!--' in line:
            comment = True
        if comment:
            if '-->' in line:
                comment = False
            continue
        if line.startswith('## '):
            flush()
            inside = re.match(r'^## *changelog\b', line, re.IGNORECASE) is not None
            kind = ''
            continue
        if not inside:
            continue
        if line.startswith('### '):
            flush()
            kind = ''
            if '|' in line:
                continue
            match = KIND_HEADING.match(line)
            if match:
                kind = match.group(1)
            continue
        if re.match(r'^[-*] ', line):
            flush()
            entry = line
            continue
        if line.strip() == '':
            flush()
            continue
        if entry:
            entry = f'{entry}\n{line}'
    flush()
    return {name: items for name, items in entries.items() if items}


def requests_minor(written, parsed):
    if parsed.get('Added') or parsed.get('Removed'):
        return True
    return MINOR_HEADING.search(written) is not None


def next_version(latest, minor, major):
    if latest is None:
        return '0.1.0', 'the first release'
    current_major, current_minor, current_patch = parse_version(latest)
    if major:
        version = format_version((current_major + 1, 0, 0))
        return version, 'asked for by hand'
    if minor:
        version = format_version((current_major, current_minor + 1, 0))
        return version, 'something was added or removed'
    version = format_version((current_major, current_minor, current_patch + 1))
    return version, 'fixes and changes only'


def render_collected(parsed):
    blocks = []
    for kind in KINDS:
        items = parsed.get(kind) or []
        if items:
            blocks.append(f'### {kind}\n\n' + '\n'.join(items))
    return '\n\n'.join(blocks)


def release_section(written, parsed):
    parts = [part for part in (written.strip('\n'), render_collected(parsed)) if part]
    return '\n\n'.join(parts)


def date_changelog(original, version, today, section):
    parse_version(version)
    lines = original.splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if line.startswith('## [Unreleased]'))
    except StopIteration as error:
        raise ValueError('CHANGELOG.md has no Unreleased heading') from error
    previous = []
    for index, line in enumerate(lines[start + 1 :]):
        if line.startswith('## ['):
            previous = lines[start + 1 + index :]
            break
    preamble = '\n'.join(lines[:start]).rstrip('\n')
    body = section.strip('\n')
    heading = f'## [Unreleased]\n\n## [{version}] - {today}'
    if body:
        heading = f'{heading}\n\n{body}'
    chunks = [chunk for chunk in (preamble, heading, '\n'.join(previous)) if chunk]
    return '\n\n'.join(chunks) + '\n'
