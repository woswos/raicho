from automation.output import quiet
from automation.paths import REPOSITORY_ROOT
from automation.quality.files import (
    CONFIGURATION_SUFFIXES,
    JAVASCRIPT_SUFFIXES,
    TYPESCRIPT_SUFFIXES,
    require_tools,
    run,
)
from automation.quality.projects import typescript_projects


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
            if path.suffix in JAVASCRIPT_SUFFIXES | TYPESCRIPT_SUFFIXES or path.suffix in CONFIGURATION_SUFFIXES
        ]
        if sources:
            mode = '--write' if action == 'format' else '--check'
            run(
                [
                    'prettier',
                    mode,
                    *quiet('--log-level', 'warn'),
                    '--config',
                    REPOSITORY_ROOT / '.prettierrc.json',
                    '--ignore-path',
                    REPOSITORY_ROOT / '.prettierignore',
                    *sources,
                ],
                root,
            )
