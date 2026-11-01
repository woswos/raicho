import shlex

from automation.paths import REPOSITORY_ROOT
from automation.quality.files import bash_files, regular_file, require_tools, run


def shfmt_options():
    configuration = regular_file(REPOSITORY_ROOT / '.shfmt', 'shfmt configuration')
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
