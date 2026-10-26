import configparser
import shutil
from pathlib import Path

from automation.build.application import NODE_REPORTER, extension, run, web
from automation.build.lcov import merge, summary
from automation.build.rust_coverage import rust
from automation.paths import REPOSITORY_ROOT
from protocol.generator.cli import test_typescript

OUTPUT = Path('/tmp/raicho-coverage')
TYPESCRIPT_IGNORED = ('**/tests/**', '**/node_modules/**', '**/*_generated.*')
PYTHON_IGNORED = (
    '*/tests/*',
    '*_tests.py',
    '*_checks.py',
    '*/automation/acceptance/*',
    '*/mailprobe/*',
)


def node_coverage(name):
    return [
        '--enable-source-maps',
        '--experimental-test-coverage',
        *(f'--test-coverage-exclude={pattern}' for pattern in TYPESCRIPT_IGNORED),
        NODE_REPORTER,
        '--test-reporter-destination=stdout',
        '--test-reporter=lcov',
        f'--test-reporter-destination={OUTPUT / f"typescript-{name}.info"}',
    ]


def typescript():
    test_typescript(['--sourceMap'], node_coverage('protocol'))
    web(True, ['--source-map'], node_coverage('web'))
    extension(
        REPOSITORY_ROOT / 'extension',
        True,
        ['--source-map'],
        node_coverage('extension'),
    )


def python_configuration(directory):
    configuration = configparser.ConfigParser()
    configuration['run'] = {
        'data_file': str(directory / 'data'),
        'parallel': 'true',
        'patch': 'subprocess',
        'include': f'\n{REPOSITORY_ROOT}/*\n/tmp/*/automation/*',
        'omit': '\n'.join(PYTHON_IGNORED),
    }
    # Guard tests run copies of automation/ from temporary repositories.
    configuration['paths'] = {
        'automation': f'\n{REPOSITORY_ROOT}/automation/\n/tmp/*/automation/',
    }
    path = directory / 'coveragerc'
    with path.open('w') as handle:
        configuration.write(handle)
    return path


def python():
    directory = OUTPUT / 'python'
    directory.mkdir()
    configuration = python_configuration(directory)
    coverage = ['python3', '-B', '-m', 'coverage']
    for start, pattern in (
        ('.', '*_tests.py'),
        ('automation/quality/tests', '*tooling_checks.py'),
    ):
        run(
            [
                *coverage,
                'run',
                f'--rcfile={configuration}',
                '-m',
                'automation.build.python_tests',
                start,
                pattern,
            ]
        )
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
