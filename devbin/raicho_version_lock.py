"""Update inherited workspace versions without resolving or changing dependencies."""

import re
import tomllib

PACKAGE_START = re.compile(r'(?m)(?=^\[\[package\]\][ \t]*(?:#.*)?$)')
PACKAGE_VERSION = re.compile(r'(?m)^(version[ \t]*=[ \t]*")[^"]+("[ \t]*(?:#.*)?$)')


def workspace_package_names(root, cargo_text):
    manifest = tomllib.loads(cargo_text)
    workspace = manifest.get('workspace', {})
    paths = {root / 'Cargo.toml'} if 'package' in manifest else set()
    excluded = {
        directory.resolve()
        for pattern in workspace.get('exclude', [])
        for directory in root.glob(pattern)
    }
    for pattern in workspace.get('members', []):
        directories = list(root.glob(pattern))
        if not directories:
            raise ValueError(f'Cargo workspace member {pattern} is missing.')
        paths.update(
            directory / 'Cargo.toml'
            for directory in directories
            if directory.resolve() not in excluded
        )
    names = set()
    for path in sorted(paths):
        package = tomllib.loads(path.read_text()).get('package', {})
        if package.get('version') != {'workspace': True}:
            continue
        name = package.get('name')
        if not isinstance(name, str) or not name or name in names:
            raise ValueError(
                f'{path} has a missing or duplicate workspace package name.'
            )
        names.add(name)
    if not names:
        raise ValueError('Cargo workspace has no packages inheriting its version.')
    return names


def replace_lock_version(root, cargo_text, lock_text, version):
    declared = tomllib.loads(cargo_text)['workspace']['package']['version']
    names = workspace_package_names(root, cargo_text)
    tomllib.loads(lock_text)
    replaced = set()
    blocks = []
    for block in PACKAGE_START.split(lock_text):
        packages = tomllib.loads(block).get('package', [])
        if packages:
            package = packages[0]
            name = package.get('name')
            if name in names and 'source' not in package:
                if name in replaced or package.get('version') != declared:
                    raise ValueError(
                        f'Cargo.lock has an inconsistent entry for {name}.'
                    )
                block, count = PACKAGE_VERSION.subn(
                    lambda match: f'{match.group(1)}{version}{match.group(2)}', block
                )
                if count != 1:
                    raise ValueError(f'Cargo.lock must contain one version for {name}.')
                replaced.add(name)
        blocks.append(block)
    missing = names - replaced
    if missing:
        raise ValueError(
            f'Cargo.lock is missing workspace packages: {sorted(missing)}.'
        )
    updated = ''.join(blocks)
    for name in sorted(names):
        reference = re.compile(
            rf'(?m)^([ \t]*"{re.escape(name)} ){re.escape(declared)}'
            r'("[ \t]*,?[ \t]*(?:#.*)?$)'
        )
        updated = reference.sub(
            lambda match: f'{match.group(1)}{version}{match.group(2)}', updated
        )
    return updated
