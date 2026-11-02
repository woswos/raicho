import re
import shutil
from pathlib import Path

DESTINATIONS = {
    'rust': Path('protocol/rust/src'),
    'typescript': Path('protocol/typescript/src'),
    'web': Path('web/src'),
}


# Generated outputs share their directories with hand-written sources, so only their names mark them.
GENERATED_NAME = re.compile(r'[a-z0-9_]+_generated\.(?:rs|ts|js|d\.ts)')


def compare_outputs(generated, committed):
    staged = sorted(path.name for path in generated.iterdir())
    unmarked = [name for name in staged if not GENERATED_NAME.fullmatch(name)]
    if unmarked:
        raise ValueError(f'Generated files must be named like contract_generated.ts: {", ".join(unmarked)}.')
    changed = [
        name
        for name in staged
        if not (committed / name).is_file() or (generated / name).read_bytes() != (committed / name).read_bytes()
    ]
    stale = sorted(
        path.name
        for path in committed.glob('*_generated.*')
        if path.is_file() and GENERATED_NAME.fullmatch(path.name) and not (generated / path.name).exists()
    )
    return changed, stale


def sync_outputs(staging, root, action):
    # Every destination is compared before any is written, so a rejected output leaves the tree untouched.
    outputs = [
        (language, destination, *compare_outputs(staging / language, root / destination))
        for language, destination in DESTINATIONS.items()
    ]
    changes = []
    for language, destination, changed, stale in outputs:
        changes.extend(str(destination / name) for name in [*changed, *stale])
        if action == 'generate':
            (root / destination).mkdir(parents=True, exist_ok=True)
            for name in changed:
                shutil.copyfile(staging / language / name, root / destination / name)
            for name in stale:
                (root / destination / name).unlink()
    return changes
