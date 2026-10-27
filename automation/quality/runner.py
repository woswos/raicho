import argparse
import subprocess
import sys
from pathlib import Path

from automation.paths import REPOSITORY_ROOT
from automation.quality.files import require_tools, source_files
from automation.quality.javascript import javascript
from automation.quality.projects import rust, typecheck
from automation.quality.python import python
from automation.quality.shell import shell
from automation.quality.spelling import spelling
from automation.quality.sql import sql

LANGUAGES = ('bash', 'python', 'javascript', 'rust', 'sql')
TARGETS = (
    'lint-bash',
    'lint-python',
    'lint-javascript',
    'lint-typescript',
    'lint-rust',
    'lint-sql',
    'lint-spelling',
    'format',
    'format-check',
    *(f'format-{language}' for language in LANGUAGES),
    *(f'format-check-{language}' for language in LANGUAGES),
    'format-spelling',
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
    elif language == 'spelling':
        spelling(root, files, action)
    else:
        sql(root, files, action, REPOSITORY_ROOT)


def failure_message(error):
    name = Path(error.cmd[0]).name
    if len(error.cmd) > 1 and error.cmd[1].isalpha():
        name = f'{name} {error.cmd[1]}'
    return f'{name} exited with status {error.returncode}'


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
    except subprocess.CalledProcessError as error:
        print(f'FAIL: {failure_message(error)}', file=sys.stderr)
        sys.exit(1)
    except (ValueError, OSError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        sys.exit(1)
