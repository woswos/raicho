import shutil
import tomllib
from pathlib import Path

from automation.build.application import extension, node_reporter, run, web
from automation.build.lcov import merge, summary
from automation.build.python_suite import SUITES
from automation.build.rust_coverage import rust
from automation.paths import REPOSITORY_ROOT
from protocol.generator.cli import run_typescript_tests

COVERAGE = tomllib.loads((REPOSITORY_ROOT / 'pyproject.toml').read_text())['tool']['coverage']
OUTPUT = Path(COVERAGE['run']['data_file']).parents[1]
TYPESCRIPT_IGNORED = ('**/tests/**', '**/node_modules/**', '**/*_generated.*')


def node_coverage(name):
    return [
        '--enable-source-maps',
        '--experimental-test-coverage',
        *(f'--test-coverage-exclude={pattern}' for pattern in TYPESCRIPT_IGNORED),
        node_reporter(),
        '--test-reporter-destination=stdout',
        '--test-reporter=lcov',
        f'--test-reporter-destination={OUTPUT / f"typescript-{name}.info"}',
    ]


def typescript():
    run_typescript_tests(['--sourceMap'], node_coverage('protocol'))
    web(True, ['--source-map'], node_coverage('web'))
    extension(
        REPOSITORY_ROOT / 'extension',
        True,
        ['--source-map'],
        node_coverage('extension'),
    )


def python():
    (OUTPUT / 'python').mkdir()
    configuration = REPOSITORY_ROOT / 'pyproject.toml'
    coverage = ['python3', '-B', '-m', 'coverage']
    for suite in SUITES:
        run([*coverage, 'run', f'--rcfile={configuration}', '-m', 'automation.build.python_suite', suite])
    run([*coverage, 'combine', '--quiet', f'--rcfile={configuration}'])
    run(
        [
            *coverage,
            'lcov',
            '--quiet',
            f'--rcfile={configuration}',
            '-o',
            OUTPUT / 'python.info',
        ]
    )


def collect():
    shutil.rmtree(OUTPUT, ignore_errors=True)
    OUTPUT.mkdir(parents=True)
    rust(OUTPUT)
    typescript()
    python()


def main():
    collect()
    print('\n'.join(summary(merge(sorted(OUTPUT.glob('*.info'))))))


if __name__ == '__main__':
    main()
