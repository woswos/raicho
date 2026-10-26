import argparse
import shlex
import subprocess
import sys
from pathlib import Path

from automation.paths import REPOSITORY_ROOT
from automation.quality.files import (
    CONFIGURATION_SUFFIXES,
    JAVASCRIPT_SUFFIXES,
    TYPESCRIPT_SUFFIXES,
    bash_files,
    require_tools,
    run,
    source_files,
)
from automation.quality.projects import (
    rust,
    typecheck,
    typescript_projects,
)
from automation.quality.sql import sql


def shfmt_options():
    configuration = REPOSITORY_ROOT / '.shfmt'
    if not configuration.is_file() or configuration.is_symlink():
        raise ValueError(
            f'shfmt configuration is missing or not a regular file: {configuration}'
        )
    return shlex.split(configuration.read_text(), comments=True)


def shell(root, files, action):
    require_tools('bash', 'shellcheck', 'shfmt')
    sources = bash_files(root, files)
    if not sources:
        return
    if action == 'lint':
        for source in sources:
            run(['bash', '-n', source], root)
        run(
            ['shellcheck', '--rcfile', REPOSITORY_ROOT / '.shellcheckrc', *sources],
            root,
        )
    else:
        mode = '--write' if action == 'format' else '--diff'
        run(['shfmt', '--list', mode, *shfmt_options(), *sources], root)


def python(root, files, action):
    require_tools('ruff')
    sources = [path for path in files if path.suffix in {'.py', '.pyi'}]
    if not sources:
        return
    configuration = ['--config', REPOSITORY_ROOT / 'pyproject.toml']
    if action == 'lint':
        run(['ruff', 'check', *configuration, *sources], root)
    elif action == 'format':
        run(['ruff', 'check', '--select', 'I', '--fix', *configuration, *sources], root)
        run(['ruff', 'format', '--quiet', *configuration, *sources], root)
    else:
        run(['ruff', 'format', '--check', '--quiet', *configuration, *sources], root)


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
                    '--no-warn-ignored',
                    *sources,
                ],
                root,
            )
    else:
        sources = [
            path
            for path in files
            if path.suffix in JAVASCRIPT_SUFFIXES | TYPESCRIPT_SUFFIXES
            or path.suffix in CONFIGURATION_SUFFIXES
        ]
        if sources:
            mode = '--write' if action == 'format' else '--check'
            run(
                [
                    'prettier',
                    mode,
                    '--log-level',
                    'warn',
                    '--config',
                    REPOSITORY_ROOT / '.prettierrc.json',
                    '--ignore-path',
                    REPOSITORY_ROOT / '.prettierignore',
                    *sources,
                ],
                root,
            )


LANGUAGES = ('bash', 'python', 'javascript', 'rust', 'sql')
TARGETS = (
    'lint-bash',
    'lint-python',
    'lint-javascript',
    'lint-typescript',
    'lint-rust',
    'lint-sql',
    'format',
    'format-check',
    *(f'format-{language}' for language in LANGUAGES),
    *(f'format-check-{language}' for language in LANGUAGES),
    'typecheck',
)


def check_language(language, root, files, action, typed=False):
    if language == 'bash':
        shell(root, files, action)
    elif language == 'python':
        python(root, files, action)
    elif language == 'javascript':
        javascript(root, files, action, typed=typed)
    elif language == 'rust':
        require_tools('cargo', 'rustfmt', 'cargo-clippy')
        rust(root, files, action, REPOSITORY_ROOT)
    else:
        sql(root, files, action, REPOSITORY_ROOT)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('target', choices=TARGETS)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    require_tools('git')
    files = source_files(root)
    target = arguments.target
    if target == 'typecheck':
        require_tools('tsc')
        typecheck(root, files)
        return
    if target in {'format', 'format-check'}:
        action, languages, typed = target, LANGUAGES, False
    else:
        action, _, language = target.rpartition('-')
        typed = language == 'typescript'
        languages = ('javascript',) if typed else (language,)
    for language in languages:
        check_language(language, root, files, action, typed)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        sys.exit(1)
