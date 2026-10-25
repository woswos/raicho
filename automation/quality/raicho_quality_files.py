import os
import shutil
import subprocess
from pathlib import Path

EXCLUDED = {'.git', 'node_modules', 'target', 'dist', 'vendor', '__pycache__'}
CONFIGURATION_FILES = {
    'protocol/typescript/package.json',
    'protocol/typescript/tsconfig.json',
    'protocol/limits.json',
    'protocol/schema/connector.schema.json',
    'protocol/fixtures/control.json',
    'protocol/fixtures/depth.json',
    'protocol/fixtures/duplicates.json',
    'protocol/fixtures/handshake.json',
    'protocol/fixtures/malformed.json',
    'protocol/fixtures/parsing.json',
    'package.json',
    '.prettierrc.json',
    'compose/compose.tools.yaml',
    'compose/compose.ci.yaml',
    'compose/compose.yaml',
    'compose/compose.admin.yaml',
    'compose/compose.runtime_test.yaml',
    'compose/compose.credentials.yaml',
    'compose/compose.connector_upgrade.yaml',
    'compose/compose.extension_test.yaml',
    'compose/compose.mail_test.yaml',
    'compose/compose.mail_admin.yaml',
    'extension/mailprobe/manifest.json',
    'extension/mailprobe/package.json',
    'extension/mailprobe/tsconfig.json',
    'extension/lifecycleprobe/manifest.json',
    'extension/lifecycleprobe/package.json',
    'extension/lifecycleprobe/tsconfig.json',
    'extension/manifest.json',
    'extension/package.json',
    'extension/tsconfig.json',
    'web/package.json',
    'web/tsconfig.json',
    '.github/workflows/repository-checks.yml',
}
JAVASCRIPT_SUFFIXES = {'.js', '.mjs', '.cjs'}
TYPESCRIPT_SUFFIXES = {'.ts', '.tsx', '.mts', '.cts'}
SOURCE_SUFFIXES = (
    JAVASCRIPT_SUFFIXES
    | TYPESCRIPT_SUFFIXES
    | {
        '.py',
        '.pyi',
        '.rs',
        '.sh',
        '.bash',
        '.sql',
    }
)


def run(arguments, root, capture=False):
    return subprocess.run(
        [
            str(root / argument) if isinstance(argument, Path) else argument
            for argument in arguments
        ],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    )


def require_tools(*names):
    for name in names:
        if shutil.which(name) is None:
            raise ValueError(
                f'{name} is unavailable. Run this target in the tooling container.'
            )


def source_files(root):
    repository = subprocess.run(
        ['git', 'rev-parse', '--show-toplevel'],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if (root / '.git').exists() and repository.returncode:
        raise ValueError(
            'Git metadata is unavailable. Mount linked-worktree Git directories read-only.'
        )
    if repository.returncode == 0 and Path(repository.stdout.strip()) == root:
        output = run(
            ['git', 'ls-files', '-cz', '--others', '--exclude-standard'], root, True
        )
        paths = {Path(name) for name in output.stdout.split('\0') if name}
    else:
        paths = set()
        for directory, directories, filenames in os.walk(root):
            directories[:] = [name for name in directories if name not in EXCLUDED]
            paths.update(
                (Path(directory) / name).relative_to(root) for name in filenames
            )
    selected = sorted(
        path
        for path in paths
        if not EXCLUDED.intersection(path.parts)
        and not path.is_relative_to('assets/brand/references')
        and ((root / path).is_file() or (root / path).is_symlink())
    )
    for path in selected:
        if (root / path).is_symlink() and (
            path.suffix in SOURCE_SUFFIXES
            or not path.suffix
            or path.name == 'Cargo.toml'
            or (path.name.startswith('tsconfig') and path.suffix == '.json')
            or path.as_posix() in CONFIGURATION_FILES
        ):
            raise ValueError(
                f'Quality tools require regular source files, not symlinks: {path}'
            )
    return selected


def bash_files(root, paths):
    result = []
    for path in paths:
        if path.suffix in {'.bash', '.sh'}:
            result.append(path)
        elif not path.suffix:
            with (root / path).open('rb') as source:
                first_line = source.readline(256).strip()
            if first_line in {b'#!/bin/bash', b'#!/usr/bin/env bash', b'#!/bin/sh'}:
                result.append(path)
    return result
