import subprocess

from automation.output import quiet
from automation.quality.files import regular_file, require_tools, run


def formatted(options, root, path, source):
    result = run(
        ['sqlfluff', 'format', *options, '--stdin-filename', path.as_posix(), '-'],
        root,
        capture=True,
        stdin=source,
    ).stdout
    try:
        run(
            ['sqlfluff', 'parse', *options, '--format', 'human', '--stdin-filename', path.as_posix(), '-'],
            root,
            capture=True,
            stdin=result,
        )
    except subprocess.CalledProcessError as error:
        print(error.stdout, end='')
        raise
    return result


def sql(root, files, action, tooling_root):
    require_tools('sqlfluff')
    configuration = regular_file(tooling_root / '.sqlfluff', 'SQL configuration')
    sources = [path for path in files if path.suffix == '.sql']
    if not sources:
        print('SKIP: no owned SQL sources')
        return
    options = [
        '--ignore-local-config',
        '--config',
        configuration,
        '--nocolor',
    ]
    if action == 'lint':
        run(
            [
                'sqlfluff',
                'lint',
                *options,
                *quiet('--quiet'),
                '--disregard-sqlfluffignores',
                *sources,
            ],
            root,
        )
        return
    originals = {path: (root / path).read_text() for path in sources}
    changed = {}
    for path, original in originals.items():
        result = formatted(options, root, path, original)
        if result != original:
            changed[path] = result
    if action == 'format-check' and changed:
        raise ValueError('SQL formatting differs: ' + ', '.join(path.as_posix() for path in changed))
    if action == 'format':
        for path, contents in changed.items():
            if (root / path).read_text() != originals[path]:
                raise ValueError(f'SQL source changed during formatting: {path}')
            (root / path).write_text(contents)
