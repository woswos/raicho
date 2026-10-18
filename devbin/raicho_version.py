"""Keep the declared product version valid and shared with extension manifests."""

import re
import subprocess
import sys
from pathlib import Path

VERSION_TEXT = re.compile(
    r'(0|[1-9][0-9]{0,4})\.(0|[1-9][0-9]{0,4})\.(0|[1-9][0-9]{0,4})'
)
MANIFEST_VERSION = re.compile(r'(?<![A-Za-z0-9_])"version"\s*:\s*"[^"]*"')
WORKSPACE_VERSION = re.compile(r'^(\s*version\s*=\s*")[^"]+(".*)$')
VERSION_LIMIT = 65535


def parse_version(text):
    if not isinstance(text, str) or not VERSION_TEXT.fullmatch(text):
        raise ValueError(
            'A product version must contain three components from 0 to 65535 '
            'without leading zeros.'
        )
    parts = tuple(int(component) for component in text.split('.'))
    if any(component > VERSION_LIMIT for component in parts):
        raise ValueError(
            'A product version must contain three components from 0 to 65535 '
            'without leading zeros.'
        )
    return parts


def format_version(parts):
    if any(part > VERSION_LIMIT or part < 0 for part in parts):
        raise ValueError(
            'The next version would exceed 65535 in one component. '
            'The Thunderbird extension manifest cannot store that value.'
        )
    return '.'.join(str(part) for part in parts)


def workspace_version(text):
    section = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('[') and stripped.endswith(']'):
            section = stripped
            continue
        if section != '[workspace.package]':
            continue
        match = re.fullmatch(r'version\s*=\s*"([^"]+)"', stripped)
        if match:
            return match.group(1)
    raise ValueError('Cargo.toml is missing the workspace package version.')


def replace_workspace_version(text, version):
    parse_version(version)
    section = None
    replaced = False
    lines = []
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith('[') and stripped.endswith(']'):
            section = stripped
        if section == '[workspace.package]' and not replaced:
            match = WORKSPACE_VERSION.match(line.rstrip('\n'))
            if match:
                newline = '\n' if line.endswith('\n') else ''
                line = f'{match.group(1)}{version}{match.group(2)}{newline}'
                replaced = True
        lines.append(line)
    if not replaced:
        raise ValueError('Cargo.toml is missing the workspace package version.')
    return ''.join(lines)


def replace_manifest_version(text, version):
    parse_version(version)
    matches = list(MANIFEST_VERSION.finditer(text))
    if len(matches) != 1:
        raise ValueError('An extension manifest must contain one version.')

    def substitute(match):
        return re.sub(r'"[^"]*"$', f'"{version}"', match.group(0))

    return MANIFEST_VERSION.sub(substitute, text, count=1)


def extension_manifests(root):
    output = subprocess.check_output(
        [
            'git',
            'ls-files',
            '-z',
            '--cached',
            '--others',
            '--exclude-standard',
            '--',
            'extension',
        ],
        cwd=root,
        stderr=subprocess.PIPE,
    )
    paths = []
    for name in output.split(b'\0'):
        if not name:
            continue
        relative = name.decode()
        if relative.endswith('/manifest.json') or relative == 'extension/manifest.json':
            if '/tests/' not in f'/{relative}':
                paths.append(relative)
    return sorted(paths)


def product_version(root):
    return workspace_version((root / 'Cargo.toml').read_text())


def check_product_version(root):
    try:
        declared = product_version(root)
        parse_version(declared)
    except (OSError, ValueError) as error:
        return [str(error)]
    failures = []
    try:
        manifests = extension_manifests(root)
    except (OSError, subprocess.CalledProcessError) as error:
        return [f'Cannot list extension manifests: {error}']
    for relative in manifests:
        path = root / relative
        try:
            text = path.read_text()
            match = MANIFEST_VERSION.search(text)
            if match is None:
                failures.append(f'{relative} is missing a version.')
                continue
            found = re.search(r'"([^"]*)"$', match.group(0))
            if found is None:
                failures.append(f'{relative} is missing a version.')
                continue
            value = found.group(1)
            parse_version(value)
        except (OSError, ValueError) as error:
            failures.append(f'{relative}: {error}')
            continue
        if value != declared:
            failures.append(
                f'{relative} version {value} does not match the product version '
                f'{declared}.'
            )
    return failures


def write_product_version(root, version):
    cargo = root / 'Cargo.toml'
    cargo.write_text(replace_workspace_version(cargo.read_text(), version))
    for relative in extension_manifests(root):
        path = root / relative
        path.write_text(replace_manifest_version(path.read_text(), version))


def main():
    if len(sys.argv) > 2:
        print('FAIL: expected at most one repository root argument', file=sys.stderr)
        return 1
    root = (
        Path(sys.argv[1]).resolve()
        if len(sys.argv) == 2
        else Path(__file__).resolve().parents[1]
    )
    failures = check_product_version(root)
    for failure in failures:
        print(f'FAIL: {failure}', file=sys.stderr)
    if failures:
        return 1
    print(f'version check passed: {product_version(root)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
