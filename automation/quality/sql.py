import subprocess
import tempfile
from pathlib import Path

from automation.quality.files import require_tools, run


def check_syntax(options, root):
    try:
        run(
            ['sqlfluff', 'parse', *options, '--format', 'none', '.'], root, capture=True
        )
    except subprocess.CalledProcessError as error:
        print(error.stdout, end='')
        raise


def sql(root, files, action, tooling_root):
    require_tools('sqlfluff')
    configuration = tooling_root / '.sqlfluff'
    if not configuration.is_file() or configuration.is_symlink():
        raise ValueError(
            f'SQL configuration is missing or not a regular file: {configuration}'
        )
    sources = [path for path in files if path.suffix == '.sql']
    if not sources:
        print('SKIP: no owned SQL sources')
        return
    options = [
        '--ignore-local-config',
        '--config',
        configuration,
        '--templater',
        'raw',
        '--dialect',
        'sqlite',
        '--encoding',
        'utf-8',
        '--nocolor',
    ]
    if action == 'lint':
        run(
            [
                'sqlfluff',
                'lint',
                *options,
                '--quiet',
                '--disregard-sqlfluffignores',
                *sources,
            ],
            root,
        )
        return
    with tempfile.TemporaryDirectory(prefix='raicho-sql-format-') as directory:
        temporary_root = Path(directory)
        originals = {path: (root / path).read_bytes() for path in sources}
        for path, contents in originals.items():
            destination = temporary_root / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(contents)
        check_syntax(options, temporary_root)
        run(
            [
                'sqlfluff',
                'format',
                *options,
                '--quiet',
                '--disregard-sqlfluffignores',
                *sources,
            ],
            temporary_root,
        )
        check_syntax(options, temporary_root)
        changed = {
            path: (temporary_root / path).read_bytes()
            for path, contents in originals.items()
            if (temporary_root / path).read_bytes() != contents
        }
        if action == 'format-check' and changed:
            raise ValueError(
                'SQL formatting differs: '
                + ', '.join(path.as_posix() for path in changed)
            )
        if action == 'format':
            for path, contents in changed.items():
                if (root / path).read_bytes() != originals[path]:
                    raise ValueError(f'SQL source changed during formatting: {path}')
                (root / path).write_bytes(contents)
