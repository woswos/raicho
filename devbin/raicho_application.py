import argparse
import os
import subprocess
import tempfile
from pathlib import Path


def run(arguments, **options):
    subprocess.run(arguments, check=True, **options)


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
            'test-mail-probe',
        ),
    )
    target = parser.parse_args().target
    if target.endswith('server'):
        action = 'build' if target == 'build-server' else 'test'
        run(['cargo', action, '--workspace', '--all-targets', '--locked'])
    elif target.endswith('extension') or target == 'test-mail-probe':
        source_root = Path(
            'extension/mail_probe' if target == 'test-mail-probe' else 'extension'
        )
        with tempfile.TemporaryDirectory(prefix='raicho-extension-') as directory:
            output = Path(directory)
            run(
                [
                    'python3',
                    '-B',
                    'devbin/raicho_build_extension.py',
                    '--source-root',
                    str(source_root),
                    '--output',
                    str(output / 'raicho.xpi'),
                    '--directory',
                    str(output / 'modules'),
                ]
            )
            if target.startswith('test-'):
                variable = (
                    'RAICHO_MAIL_PROBE_BUILD_DIR'
                    if target == 'test-mail-probe'
                    else 'RAICHO_EXTENSION_BUILD_DIR'
                )
                environment = os.environ | {variable: str(output / 'modules')}
                tests = sorted(
                    str(path) for path in (source_root / 'tests').glob('*.test.mjs')
                )
                if not tests:
                    raise ValueError('No extension tests were found.')
                run(['node', '--test', *tests], env=environment)
    else:
        with tempfile.TemporaryDirectory(prefix='raicho-web-') as directory:
            run(['node', 'devbin/raicho_build_web.mjs', directory])
            if target == 'test-web':
                environment = os.environ | {'RAICHO_WEB_BUILD_DIR': directory}
                tests = sorted(str(path) for path in Path('web/tests').glob('*.mjs'))
                if not tests:
                    raise ValueError('No browser application tests were found.')
                run(['node', '--test', *tests], env=environment)


if __name__ == '__main__':
    main()
