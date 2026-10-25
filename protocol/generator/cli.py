import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from protocol.generator.validation import validate_sources

ROOT = Path(__file__).resolve().parents[2]
OUTPUTS = {
    'rust': (
        Path('protocol/rust/src'),
        ['contract_generated.rs', 'limits_generated.rs', 'diagnostics_generated.rs'],
    ),
    'typescript': (
        Path('protocol/typescript/src'),
        [
            'contract_generated.ts',
            'validator_generated.js',
            'validator_generated.d.ts',
            'limits_generated.ts',
        ],
    ),
    'web': (Path('web/src'), ['diagnostics_generated.ts']),
}


def changed_outputs(generated, committed, filenames):
    return [
        name
        for name in filenames
        if not (committed / name).is_file()
        or (generated / name).read_bytes() != (committed / name).read_bytes()
    ]


def test_typescript():
    source = ROOT / 'protocol/typescript'
    with tempfile.TemporaryDirectory(prefix='raicho-protocol-typescript-') as directory:
        subprocess.run(
            ['tsc', '--project', str(source / 'tsconfig.json'), '--outDir', directory],
            cwd=ROOT,
            check=True,
        )
        shutil.copyfile(source / 'package.json', f'{directory}/package.json')
        tests = sorted(str(path) for path in (source / 'tests').glob('*.test.mjs'))
        if not tests:
            raise ValueError('No TypeScript protocol tests were found.')
        subprocess.run(
            ['node', '--test', *tests],
            cwd=ROOT,
            env=os.environ | {'RAICHO_PROTOCOL_BUILD_DIR': directory},
            check=True,
        )


def generate(action):
    validate_sources(
        *(
            json.loads((ROOT / 'protocol' / name).read_text())
            for name in (
                'schema/connector.schema.json',
                'limits.json',
                'diagnostics.json',
            )
        )
    )
    with tempfile.TemporaryDirectory(prefix='raicho-protocol-') as temporary:
        staging = Path(temporary)
        commands = [
            [
                'cargo',
                'run',
                '--locked',
                '--package',
                'raicho-protocol-generator',
                '--',
                str(staging / 'rust'),
            ],
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
                    shutil.copyfile(
                        staging / language / name, ROOT / destination / name
                    )
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
