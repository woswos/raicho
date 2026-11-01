import shutil
import subprocess
from pathlib import Path

EXCLUDED = {'.git', 'node_modules', 'target', 'dist', 'vendor', '__pycache__'}
CONFIGURATION_SUFFIXES = {'.json', '.yaml', '.yml'}
JAVASCRIPT_SUFFIXES = {'.js', '.mjs', '.cjs'}
TYPESCRIPT_SUFFIXES = {'.ts', '.tsx', '.mts', '.cts'}


def run(arguments, root, capture=False, stdin=None):
    return subprocess.run(
        [str(root / argument) if isinstance(argument, Path) else argument for argument in arguments],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        input=stdin,
    )


def require_tools(*names):
    for name in names:
        if shutil.which(name) is None:
            raise ValueError(f'{name} is unavailable. Run this target in the tooling container.')


def regular_file(path, description):
    if not path.is_file() or path.is_symlink():
        raise ValueError(f'{description} is missing or not a regular file: {path}')
    return path


def source_files(root):
    repository = subprocess.run(
        ['git', 'rev-parse', '--show-toplevel'],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if repository.returncode or Path(repository.stdout.strip()) != root:
        raise ValueError(f'Git metadata is unavailable for {root}. Mount linked-worktree Git directories read-only.')
    output = run(['git', 'ls-files', '-cz', '--others', '--exclude-standard'], root, True)
    paths = {Path(name) for name in output.stdout.split('\0') if name}
    selected = sorted(
        path
        for path in paths
        if not EXCLUDED.intersection(path.parts)
        and not path.is_relative_to('assets/brand/references')
        and ((root / path).is_file() or (root / path).is_symlink())
    )
    for path in selected:
        if (root / path).is_symlink():
            raise ValueError(f'Quality tools require regular files, not symlinks: {path}')
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
