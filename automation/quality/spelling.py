from automation.paths import REPOSITORY_ROOT
from automation.quality.files import require_tools, run


def spelling(root, files, action):
    require_tools('typos')
    configuration = REPOSITORY_ROOT / '.typos.toml'
    if not configuration.is_file() or configuration.is_symlink():
        raise ValueError(f'typos configuration is missing or not a regular file: {configuration}')
    if not files:
        return
    mode = '--write-changes' if action == 'format' else '--format=brief'
    run(['typos', '--isolated', '--config', configuration, '--force-exclude', mode, *files], root)
