import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from automation.paths import REPOSITORY_ROOT

BENCHMARK = ['cargo', 'bench', '--workspace', '--bench', '*', '--locked']
NODE_REPORTER = f'--test-reporter={REPOSITORY_ROOT / "automation/build/node_reporter.mjs"}'


def run(arguments, **options):
    return subprocess.run(arguments, cwd=REPOSITORY_ROOT, check=True, **options)


def cargo_test(arguments, env=None):
    command = ['cargo', 'test', *arguments]
    if (env or os.environ).get('CARGO_TERM_QUIET') != 'true':
        return run(command, env=env)
    result = subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if result.returncode:
        sys.stdout.write(result.stdout)
        raise subprocess.CalledProcessError(result.returncode, command)
    print(test_summary(result.stdout), flush=True)
    return result


def cargo_bench():
    if os.environ.get('CARGO_TERM_QUIET') != 'true':
        return run(BENCHMARK)
    # Criterion reports progress on stderr and results on stdout.
    result = subprocess.run(BENCHMARK, cwd=REPOSITORY_ROOT, stderr=subprocess.PIPE, text=True, check=False)
    if result.returncode:
        sys.stderr.write(result.stderr)
        raise subprocess.CalledProcessError(result.returncode, BENCHMARK)
    return result


def test_summary(output):
    results = re.findall(r'^test result: ok\. (\d+) passed', output, re.MULTILINE)
    return f'Rust: {sum(map(int, results))} tests passed in {len(results)} test binaries'


def extension(
    source_root,
    testing=False,
    build_arguments=(),
    test_arguments=(NODE_REPORTER,),
):
    with tempfile.TemporaryDirectory(prefix='raicho-extension-') as directory:
        output = Path(directory)
        run(
            [
                'node',
                str(REPOSITORY_ROOT / 'extension/build.mjs'),
                '--source-root',
                str(source_root),
                '--output',
                str(output / 'raicho.xpi'),
                '--directory',
                str(output / 'modules'),
                *build_arguments,
            ]
        )
        if testing:
            environment = os.environ | {'RAICHO_EXTENSION_BUILD_DIR': str(output / 'modules')}
            tests = sorted(str(path) for path in (source_root / 'tests').glob('*.test.mjs'))
            if not tests:
                raise ValueError('No extension tests were found.')
            run(['node', '--test', *test_arguments, *tests], env=environment)


def web(testing=False, build_arguments=(), test_arguments=(NODE_REPORTER,)):
    with tempfile.TemporaryDirectory(prefix='raicho-web-') as directory:
        run(
            [
                'node',
                str(REPOSITORY_ROOT / 'web/build.mjs'),
                directory,
                *build_arguments,
            ]
        )
        if testing:
            environment = os.environ | {'RAICHO_WEB_BUILD_DIR': directory}
            tests = sorted(str(path) for path in (REPOSITORY_ROOT / 'web/tests').glob('*.mjs'))
            if not tests:
                raise ValueError('No browser application tests were found.')
            run(['node', '--test', *test_arguments, *tests], env=environment)


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
            'benchmark',
        ),
    )
    target = parser.parse_args().target
    if target == 'benchmark':
        cargo_bench()
    elif target.endswith('server'):
        arguments = ['--workspace', '--all-targets', '--locked']
        if target == 'build-server':
            run(['cargo', 'build', *arguments])
        else:
            cargo_test(arguments)
    elif target.endswith('extension') or target == 'test-mailprobe':
        if target == 'test-mailprobe':
            extension(REPOSITORY_ROOT / 'mailprobe', testing=True)
        else:
            extension(REPOSITORY_ROOT / 'extension', testing=target.startswith('test-'))
    else:
        web(testing=target == 'test-web')


if __name__ == '__main__':
    main()
