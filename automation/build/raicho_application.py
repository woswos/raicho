import argparse
import os
import subprocess
import tempfile
from pathlib import Path

from automation.raicho_paths import REPOSITORY_ROOT


def run(arguments, **options):
    subprocess.run(arguments, cwd=REPOSITORY_ROOT, check=True, **options)


def extension(source_root, testing=False):
    with tempfile.TemporaryDirectory(prefix='raicho-extension-') as directory:
        output = Path(directory)
        run(
            [
                'node',
                str(REPOSITORY_ROOT / 'extension/raicho_build_extension.mjs'),
                '--source-root',
                str(source_root),
                '--output',
                str(output / 'raicho.xpi'),
                '--directory',
                str(output / 'modules'),
            ]
        )
        if testing:
            environment = os.environ | {
                'RAICHO_EXTENSION_BUILD_DIR': str(output / 'modules')
            }
            tests = sorted(
                str(path) for path in (source_root / 'tests').glob('*.test.mjs')
            )
            if not tests:
                raise ValueError('No extension tests were found.')
            run(['node', '--test', *tests], env=environment)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'target',
        choices=(
            'build-server',
            'build-web',
            'build-extension',
            'test-server',
            'test-web',
            'test-extension',
            'test-mailprobe',
        ),
    )
    target = parser.parse_args().target
    if target.endswith('server'):
        action = 'build' if target == 'build-server' else 'test'
        run(['cargo', action, '--workspace', '--all-targets', '--locked'])
    elif target.endswith('extension') or target == 'test-mailprobe':
        if target == 'test-mailprobe':
            extension(REPOSITORY_ROOT / 'extension/mailprobe', testing=True)
        else:
            extension(REPOSITORY_ROOT / 'extension', testing=target.startswith('test-'))
    else:
        with tempfile.TemporaryDirectory(prefix='raicho-web-') as directory:
            run(
                [
                    'node',
                    str(REPOSITORY_ROOT / 'web/raicho_build_web.mjs'),
                    directory,
                ]
            )
            if target == 'test-web':
                environment = os.environ | {'RAICHO_WEB_BUILD_DIR': directory}
                tests = sorted(
                    str(path) for path in (REPOSITORY_ROOT / 'web/tests').glob('*.mjs')
                )
                if not tests:
                    raise ValueError('No browser application tests were found.')
                run(['node', '--test', *tests], env=environment)


if __name__ == '__main__':
    main()
