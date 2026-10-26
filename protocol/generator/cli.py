import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from protocol.generator.validation import validate_sources, validate_status

ROOT = Path(__file__).resolve().parents[2]
NODE_REPORTER = f'--test-reporter={ROOT / "automation/build/node_reporter.mjs"}'
# The same selection as every other debug build reuses its artifacts.
CARGO_BUILD = ['cargo', 'build', '--workspace', '--all-targets', '--locked']
OUTPUTS = {
    'rust': (
        Path('protocol/rust/src'),
        ['contract_generated.rs', 'limits_generated.rs', 'diagnostics_generated.rs'],
    ),
    'typescript': (
        Path('protocol/typescript/src'),
        [
            'contract_generated.ts',
            'diagnostics_generated.ts',
            'validator_generated.js',
            'validator_generated.d.ts',
            'limits_generated.ts',
        ],
    ),
    'web': (
        Path('web/src'),
        [
            'status_generated.ts',
            'status_validator_generated.js',
            'status_validator_generated.d.ts',
        ],
    ),
}


def changed_outputs(generated, committed, filenames):
    return [
        name
        for name in filenames
        if not (committed / name).is_file() or (generated / name).read_bytes() != (committed / name).read_bytes()
    ]


def node_reporter():
    return '--test-reporter=spec' if os.environ.get('VERBOSE') else NODE_REPORTER


def test_typescript(compiler_arguments=(), test_arguments=None):
    source = ROOT / 'protocol/typescript'
    with tempfile.TemporaryDirectory(prefix='raicho-protocol-typescript-') as directory:
        subprocess.run(
            [
                'tsc',
                '--project',
                str(source / 'tsconfig.json'),
                '--outDir',
                directory,
                *compiler_arguments,
            ],
            cwd=ROOT,
            check=True,
        )
        shutil.copyfile(source / 'package.json', f'{directory}/package.json')
        tests = sorted(str(path) for path in (source / 'tests').glob('*.test.mjs'))
        if not tests:
            raise ValueError('No TypeScript protocol tests were found.')
        reporter = (node_reporter(),) if test_arguments is None else test_arguments
        subprocess.run(
            ['node', '--test', *reporter, *tests],
            cwd=ROOT,
            env=os.environ | {'RAICHO_PROTOCOL_BUILD_DIR': directory},
            check=True,
        )


def generate(action):
    schema, status, limits, diagnostics = (
        json.loads((ROOT / 'protocol' / name).read_text())
        for name in (
            'schema/connector.schema.json',
            'schema/status.schema.json',
            'limits.json',
            'diagnostics.json',
        )
    )
    validate_sources(schema, limits, diagnostics)
    validate_status(status, diagnostics)
    with tempfile.TemporaryDirectory(prefix='raicho-protocol-') as temporary:
        staging = Path(temporary)
        generator = Path(os.environ.get('CARGO_TARGET_DIR', ROOT / 'target')) / 'debug/raicho-protocol-generator'
        commands = [
            CARGO_BUILD,
            [str(generator), str(staging / 'rust')],
            [
                'node',
                str(ROOT / 'protocol/generator/generate_typescript.mjs'),
                str(staging / 'typescript'),
                str(staging / 'web'),
            ],
        ]
        for command in commands:
            subprocess.run(command, cwd=ROOT, check=True)
        changes = []
        for language, (destination, filenames) in OUTPUTS.items():
            changed = changed_outputs(staging / language, ROOT / destination, filenames)
            changes.extend(str(destination / name) for name in changed)
            if action == 'generate':
                (ROOT / destination).mkdir(parents=True, exist_ok=True)
                for name in changed:
                    shutil.copyfile(staging / language / name, ROOT / destination / name)
        if action == 'check' and changes:
            raise ValueError(
                'Generated protocol outputs drifted: '
                + ', '.join(changes)
                + '. Run make generate-protocol through the Docker format service.'
            )
    print(f'Protocol {action} passed.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['generate', 'check', 'test'])
    action = parser.parse_args().action
    try:
        if action == 'test':
            test_typescript()
        else:
            generate(action)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'FAIL: Protocol {action} failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
