import argparse
import subprocess
import sys
from pathlib import Path

from raicho_quality_files import (
    CONFIGURATION_FILES,
    JAVASCRIPT_SUFFIXES,
    TYPESCRIPT_SUFFIXES,
    bash_files,
    require_tools,
    run,
    source_files,
)
from raicho_quality_projects import rust, typecheck, typescript_projects
from raicho_quality_sql import sql

TOOLING_ROOT = Path(__file__).resolve().parent.parent


def shell(root, files, action):
    require_tools('bash', 'shellcheck', 'shfmt')
    sources = bash_files(root, files)
    if not sources:
        return
    if action == 'lint':
        for source in sources:
            run(['bash', '-n', source], root)
        run(['shellcheck', '--rcfile', TOOLING_ROOT / '.shellcheckrc', *sources], root)
    else:
        mode = '-w' if action == 'format' else '-d'
        run(['shfmt', '-ln', 'bash', '-i', '4', '-ci', mode, *sources], root)


def python(root, files, action):
    require_tools('ruff')
    sources = [path for path in files if path.suffix in {'.py', '.pyi'}]
    if not sources:
        return
    configuration = ['--config', TOOLING_ROOT / 'pyproject.toml']
    if action == 'lint':
        run(['ruff', 'check', *configuration, *sources], root)
    elif action == 'format':
        run(['ruff', 'check', '--select', 'I', '--fix', *configuration, *sources], root)
        run(['ruff', 'format', *configuration, *sources], root)
    else:
        run(['ruff', 'format', '--check', *configuration, *sources], root)


def javascript(root, files, action, typed=False):
    require_tools('eslint', 'prettier', 'tsc')
    suffixes = TYPESCRIPT_SUFFIXES if typed else JAVASCRIPT_SUFFIXES
    sources = [path for path in files if path.suffix in suffixes]
    if action == 'lint':
        if typed:
            typescript_projects(root, files)
        if sources:
            run(
                [
                    'eslint',
                    '--config',
                    '/opt/quality/eslint.config.mjs',
                    '--max-warnings',
                    '0',
                    *sources,
                ],
                root,
            )
    else:
        sources = [
            path
            for path in files
            if path.suffix in JAVASCRIPT_SUFFIXES | TYPESCRIPT_SUFFIXES
            or path.as_posix() in CONFIGURATION_FILES
        ]
        if sources:
            mode = '--write' if action == 'format' else '--check'
            run(
                [
                    'prettier',
                    mode,
                    '--config',
                    TOOLING_ROOT / '.prettierrc.json',
                    '--ignore-path',
                    TOOLING_ROOT / '.prettierignore',
                    *sources,
                ],
                root,
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument(
        'target',
        choices=(
            'lint-bash',
            'lint-python',
            'lint-javascript',
            'lint-typescript',
            'lint-rust',
            'lint-sql',
            'format',
            'format-sql',
            'format-check',
            'format-check-rust',
            'format-check-javascript',
            'format-check-sql',
            'typecheck',
        ),
    )
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    require_tools('git')
    files = source_files(root)
    target = arguments.target
    if target == 'typecheck':
        require_tools('tsc')
        typecheck(root, files)
        return
    action = (
        'lint'
        if target.startswith('lint-')
        else ('format-check' if target.startswith('format-check') else 'format')
    )
    if target in {'format', 'format-check', 'lint-bash'}:
        shell(root, files, action)
    if target in {'format', 'format-check', 'lint-python'}:
        python(root, files, action)
    if target in {
        'format',
        'format-check',
        'format-check-javascript',
        'lint-javascript',
        'lint-typescript',
    }:
        javascript(root, files, action, typed=target == 'lint-typescript')
    if target in {'format', 'format-check', 'format-check-rust', 'lint-rust'}:
        require_tools('cargo', 'rustfmt', 'cargo-clippy')
        rust(root, files, action, TOOLING_ROOT)
    if target in {
        'format',
        'format-sql',
        'format-check',
        'format-check-sql',
        'lint-sql',
    }:
        sql(root, files, action, TOOLING_ROOT)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        sys.exit(1)
