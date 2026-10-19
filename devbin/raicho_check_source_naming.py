"""Keep first-party source filenames consistent across language boundaries."""

import re
import subprocess
import sys
from pathlib import Path

from raicho_migration_naming import migration_failures
from raicho_shell_shebang import shell_header

EXCLUDED = {'.git', 'node_modules', 'target', 'dist', 'vendor', '__pycache__'}
JAVASCRIPT_SUFFIXES = {'.js', '.mjs', '.cjs', '.jsx'}
TYPESCRIPT_SUFFIXES = {'.ts', '.tsx', '.mts', '.cts'}
SOURCE_SUFFIXES = (
    JAVASCRIPT_SUFFIXES
    | TYPESCRIPT_SUFFIXES
    | {
        '.rs',
        '.py',
        '.pyi',
        '.bash',
        '.sh',
        '.sql',
        '.html',
        '.css',
    }
)
CANONICAL_NAMES = {
    '.eslintrc.js',
    '.eslintrc.cjs',
    '.prettierrc.js',
    '.prettierrc.cjs',
    '.prettierrc.mjs',
}
SNAKE_NAME = re.compile(r'[a-z0-9]+(?:_[a-z0-9]+)*')


def valid_filename(path):
    if path.name in CANONICAL_NAMES:
        return True
    if path.name != path.name.lower():
        return False
    if path.suffix in {'.py', '.pyi'} and path.stem in {'__init__', '__main__'}:
        return True
    stem = path.stem
    if SNAKE_NAME.fullmatch(stem):
        return True
    base, separator, qualifier = stem.rpartition('.')
    if not separator or not SNAKE_NAME.fullmatch(base):
        return False
    if path.suffix in JAVASCRIPT_SUFFIXES | TYPESCRIPT_SUFFIXES:
        if qualifier in {'test', 'spec', 'config'}:
            return True
        return qualifier == 'd' and path.suffix in {'.ts', '.mts', '.cts'}
    return qualifier == 'module' and path.suffix == '.css'


def is_source(root, path):
    if path.suffix.lower() in SOURCE_SUFFIXES:
        return True
    disk = root / path
    if path.suffix or disk.is_symlink() or not disk.is_file():
        return False
    with disk.open('rb') as source:
        return shell_header(source.readline(256))


def repository_paths(root):
    repository = subprocess.check_output(
        ['git', 'rev-parse', '--show-toplevel'],
        cwd=root,
        stderr=subprocess.PIPE,
        text=True,
    )
    if Path(repository.strip()).resolve() != root:
        raise ValueError(f'expected Git repository root: {root}')
    output = subprocess.check_output(
        ['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
        cwd=root,
        stderr=subprocess.PIPE,
        text=True,
    )
    return sorted({Path(name) for name in output.split('\0') if name})


def check_source_naming(root):
    root = Path(root).resolve()
    try:
        paths = repository_paths(root)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        return [f'cannot inspect Git repository {root}: {error}']
    failures = migration_failures(paths)
    for path in paths:
        if EXCLUDED.intersection(path.parts[:-1]) or path.is_relative_to(
            'assets/brand/references'
        ):
            continue
        try:
            if is_source(root, path) and not valid_filename(path):
                failure = f'{path} must use lowercase snake_case'
                replacement = path.with_name(path.name.replace('-', '_'))
                if replacement != path and valid_filename(replacement):
                    failure += f': {replacement.name}'
                failures.append(failure)
        except OSError as error:
            failures.append(f'cannot inspect source filename {path}: {error}')
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
    failures = check_source_naming(root)
    for failure in failures:
        print(f'FAIL: {failure}', file=sys.stderr)
    if failures:
        return 1
    print('source-naming check passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
