import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from protocol.generator.raicho_protocol_schema import validate_sources
from protocol.generator.raicho_protocol_typescript import test_typescript

ROOT = Path(__file__).resolve().parents[2]
OUTPUTS = {
    'rust': (
        Path('protocol/rust/src'),
        ['generated.rs', 'limits_generated.rs'],
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
}


def changed_outputs(generated, committed, filenames):
    return [
        name
        for name in filenames
        if not (committed / name).is_file()
        or (generated / name).read_bytes() != (committed / name).read_bytes()
    ]


def generate(action):
    validate_sources(
        json.loads((ROOT / 'protocol/schema/connector.schema.json').read_text()),
        json.loads((ROOT / 'protocol/limits.json').read_text()),
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
                str(ROOT / 'protocol/generator/raicho_generate_protocol.mjs'),
                str(staging / 'typescript'),
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
            subprocess.run(
                [
                    'cargo',
                    'test',
                    '--locked',
                    '--package',
                    'raicho-protocol',
                    '--package',
                    'raicho-protocol-generator',
                ],
                cwd=ROOT,
                check=True,
            )
            test_typescript(ROOT)
        else:
            generate(action)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'FAIL: Protocol {action} failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
