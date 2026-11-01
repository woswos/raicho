from automation.output import quiet
from automation.paths import REPOSITORY_ROOT
from automation.quality.files import require_tools, run


def python(root, files, action):
    require_tools('ruff')
    sources = [path for path in files if path.suffix in {'.py', '.pyi'}]
    if not sources:
        return
    configuration = ['--config', REPOSITORY_ROOT / 'pyproject.toml']
    if action == 'lint':
        run(['ruff', 'check', *quiet('--quiet'), *configuration, *sources], root)
    elif action == 'format':
        run(
            [
                'ruff',
                'check',
                *quiet('--quiet'),
                '--select',
                'I',
                '--fix',
                *configuration,
                *sources,
            ],
            root,
        )
        run(['ruff', 'format', *quiet('--quiet'), *configuration, *sources], root)
    else:
        run(['ruff', 'format', '--check', *quiet('--quiet'), *configuration, *sources], root)
