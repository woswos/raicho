import json
import os
from pathlib import Path

from automation.build.application import cargo_test, run

RUST_TARGET = Path(os.environ.get('CARGO_TARGET_DIR', '/tmp/raicho-target')).parent / 'coverage-target'
RUST_IGNORED = r'(/registry/|^/rustc/|/tests/|/benches/|_generated\.rs$)'


def instrumented_executables(messages):
    return sorted(
        {
            message['executable']
            for message in map(json.loads, messages.splitlines())
            if message.get('reason') == 'compiler-artifact' and message.get('executable')
        }
    )


def rust(output):
    profiles = output / 'rust'
    profiles.mkdir()
    environment = os.environ | {
        'RUSTFLAGS': '-C instrument-coverage',
        'CARGO_TARGET_DIR': str(RUST_TARGET),
        'LLVM_PROFILE_FILE': str(profiles / '%p-%m.profraw'),
    }
    arguments = ['--workspace', '--all-targets', '--locked']
    cargo_test(arguments, env=environment)
    listing = run(
        ['cargo', 'test', *arguments, '--no-run', '--message-format=json'],
        env=environment,
        capture_output=True,
        text=True,
    ).stdout
    executables = instrumented_executables(listing)
    library = run(['rustc', '--print', 'target-libdir'], capture_output=True, text=True).stdout.strip()
    tools = Path(library).parent / 'bin'
    merged = profiles / 'merged.profdata'
    run(
        [
            tools / 'llvm-profdata',
            'merge',
            '-sparse',
            *sorted(profiles.glob('*.profraw')),
            '-o',
            merged,
        ]
    )
    report = run(
        [
            tools / 'llvm-cov',
            'export',
            '-format=lcov',
            f'-instr-profile={merged}',
            f'-ignore-filename-regex={RUST_IGNORED}',
            executables[0],
            *(f'-object={executable}' for executable in executables[1:]),
        ],
        capture_output=True,
        text=True,
    ).stdout
    (output / 'rust.info').write_text(report)
