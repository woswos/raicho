from automation.paths import REPOSITORY_ROOT
from automation.quality.files import regular_file, require_tools, run


def spelling(root, files, action):
    require_tools('typos')
    configuration = regular_file(REPOSITORY_ROOT / '.typos.toml', 'typos configuration')
    if not files:
        return
    mode = '--write-changes' if action == 'format' else '--format=brief'
    run(['typos', '--isolated', '--config', configuration, '--force-exclude', mode, *files], root)
