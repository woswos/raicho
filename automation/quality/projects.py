import hashlib
import json
import os
from pathlib import Path

from automation.quality.files import TYPESCRIPT_SUFFIXES, run


def rust_projects(root, files):
    manifests = [path for path in files if path.name == 'Cargo.toml']
    sources = [path for path in files if path.suffix == '.rs']
    if not manifests and not sources:
        print('SKIP: Rust is not applicable (no Cargo manifests or Rust sources).')
        return []
    for source in sources:
        if not any(source.is_relative_to(manifest.parent) for manifest in manifests):
            raise ValueError(f'Rust source has no Cargo.toml: {source}')
    projects = set()
    for manifest in manifests:
        result = run(
            [
                'cargo',
                'metadata',
                '--manifest-path',
                manifest,
                '--no-deps',
                '--locked',
                '--format-version',
                '1',
            ],
            root,
            True,
        )
        metadata = json.loads(result.stdout)
        workspace = Path(metadata['workspace_root'])
        if not workspace.is_relative_to(root):
            raise ValueError(f'Cargo workspace escapes the source root: {manifest}')
        if not (workspace / 'Cargo.lock').is_file():
            raise ValueError(f'Cargo.lock is required: {workspace}')
        projects.add(workspace / 'Cargo.toml')
    return sorted(projects)


def typescript_projects(root, files):
    sources = {root / path for path in files if path.suffix in TYPESCRIPT_SUFFIXES}
    if not sources:
        print('SKIP: TypeScript is not applicable (no TypeScript sources).')
        return []
    configurations = [
        path
        for path in files
        if path.name.startswith('tsconfig') and path.suffix == '.json'
    ]
    if not configurations:
        raise ValueError('TypeScript sources require a tsconfig.json project.')
    covered = set()
    for configuration in configurations:
        result = run(
            ['tsc', '--project', configuration, '--noEmit', '--listFilesOnly'],
            root,
            True,
        )
        covered.update(Path(line).resolve() for line in result.stdout.splitlines())
    missing = sources - covered
    if missing:
        names = ', '.join(str(path.relative_to(root)) for path in sorted(missing))
        raise ValueError(f'TypeScript sources excluded from every tsconfig: {names}')
    return configurations


def typecheck(root, files):
    for configuration in typescript_projects(root, files):
        cache_key = hashlib.sha256(str(root / configuration).encode()).hexdigest()
        run(
            [
                'tsc',
                '--project',
                configuration,
                '--noEmit',
                '--incremental',
                '--tsBuildInfoFile',
                f'/tmp/{cache_key}.tsbuildinfo',
            ],
            root,
        )


def rust(root, files, action, tooling_root):
    for manifest in rust_projects(root, files):
        if action == 'lint':
            workspace_key = hashlib.sha256(str(manifest).encode()).hexdigest()
            target = (
                Path(os.environ.get('CARGO_TARGET_DIR', '/tmp/raicho-target'))
                / workspace_key
            )
            run(
                [
                    'cargo',
                    'clippy',
                    '--manifest-path',
                    manifest,
                    '--workspace',
                    '--all-targets',
                    '--locked',
                    '--target-dir',
                    target,
                ],
                root,
            )
        else:
            arguments = ['cargo', 'fmt', '--manifest-path', manifest, '--all', '--']
            if action == 'format-check':
                arguments.append('--check')
            arguments.extend(['--config-path', tooling_root / 'rustfmt.toml'])
            run(arguments, root)
    if action != 'lint':
        for source in files:
            if source.suffix == '.rs':
                arguments = ['rustfmt', '--config-path', tooling_root / 'rustfmt.toml']
                if action == 'format-check':
                    arguments.append('--check')
                run([*arguments, source], root)
