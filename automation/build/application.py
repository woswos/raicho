import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from automation.paths import REPOSITORY_ROOT
from protocol.generator.cli import node_reporter

BENCHMARK = ['cargo', 'bench', '--workspace', '--bench', '*', '--locked']
CARGO_WORKSPACE = ['--workspace', '--all-targets', '--locked']


def cargo_filter():
    name = os.environ.get('TEST')
    return ['--', name] if name else []


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


def node_test(test_arguments, tests, environment):
    arguments = (node_reporter(),) if test_arguments is None else test_arguments
    run(['node', '--test', *arguments, *tests], env=environment)


def extension(
    source_root,
    testing=False,
    build_arguments=(),
    test_arguments=None,
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
            node_test(test_arguments, tests, environment)


def web(testing=False, build_arguments=(), test_arguments=None):
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
            node_test(test_arguments, tests, environment)


# Each entry looks its function up when called, so tests can patch the module.
TARGETS = {
    'build-server': lambda: run(['cargo', 'build', *CARGO_WORKSPACE]),
    'test-server': lambda: cargo_test([*CARGO_WORKSPACE, *cargo_filter()]),
    'build-web': lambda: web(testing=False),
    'test-web': lambda: web(testing=True),
    'build-extension': lambda: extension(REPOSITORY_ROOT / 'extension', testing=False),
    'test-extension': lambda: extension(REPOSITORY_ROOT / 'extension', testing=True),
    'test-mailprobe': lambda: extension(REPOSITORY_ROOT / 'mailprobe', testing=True),
    'benchmark': lambda: cargo_bench(),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('target', choices=TARGETS)
    TARGETS[parser.parse_args().target]()


if __name__ == '__main__':
    main()
