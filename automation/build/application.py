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
        'target', choices=('build-server', 'build-web', 'test-server', 'test-web')
    )
    target = parser.parse_args().target
    if target.endswith('server'):
        action = 'build' if target == 'build-server' else 'test'
        run(['cargo', action, '--workspace', '--all-targets', '--locked'])
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
