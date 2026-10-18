import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
EXTENSION_ROOT = REPOSITORY_ROOT / 'extension'


def prepare_directory(directory):
    if not directory.is_absolute():
        raise ValueError('The extension output directory must be absolute.')
    if directory.exists() and (not directory.is_dir() or any(directory.iterdir())):
        raise ValueError('The extension output directory must be empty.')
    directory.mkdir(parents=True, exist_ok=True)


def extension_manifest(version, source_root):
    manifest = json.loads((source_root / 'manifest.json').read_text())
    if not isinstance(manifest, dict):
        raise ValueError('The extension manifest must be an object.')
    selected_version = manifest.get('version') if version is None else version
    if (
        not isinstance(selected_version, str)
        or not re.fullmatch(
            r'(0|[1-9][0-9]{0,4})\.(0|[1-9][0-9]{0,4})\.(0|[1-9][0-9]{0,4})',
            selected_version,
        )
        or any(int(component) > 65535 for component in selected_version.split('.'))
    ):
        raise ValueError(
            'The extension version must contain three components from 0 to 65535 '
            'without leading zeros.'
        )
    manifest['version'] = selected_version
    return manifest


def compile_extension(directory, manifest, source_root):
    subprocess.run(
        [
            'tsc',
            '--project',
            str(source_root / 'tsconfig.json'),
            '--outDir',
            str(directory),
        ],
        check=True,
    )
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    shutil.copyfile(source_root / 'background.html', directory / 'background.html')
    options_page = manifest.get('options_ui', {}).get('page')
    if options_page is not None:
        if not isinstance(options_page, str) or not re.fullmatch(
            r'[a-z_]+\.html', options_page
        ):
            raise ValueError('The options page must be a root-level HTML file.')
        shutil.copyfile(source_root / options_page, directory / options_page)


def build(
    output=None,
    version=None,
    directory=None,
    output_directory=None,
    source_root=EXTENSION_ROOT,
):
    manifest = extension_manifest(version, source_root)
    if (output is None) == (output_directory is None):
        raise ValueError('Choose exactly one extension output mode.')
    if output_directory is not None:
        if directory is not None and (
            directory.is_relative_to(output_directory)
            or output_directory.is_relative_to(directory)
        ):
            raise ValueError(
                'Artifact and compiled output directories must be separate.'
            )
        prepare_directory(output_directory)
        output = output_directory / f'raicho-{manifest["version"]}.xpi'
    if not output.is_absolute() or output.suffix != '.xpi' or output.exists():
        raise ValueError('Supply an absolute, unused .xpi output path.')
    if directory is not None:
        prepare_directory(directory)
        if output.is_relative_to(directory):
            raise ValueError('The XPI must be outside the compiled output directory.')
    with tempfile.TemporaryDirectory(prefix='raicho-extension-') as temporary:
        compiled = Path(temporary)
        compile_extension(compiled, manifest, source_root)
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_STORED) as archive:
            for source in sorted(compiled.rglob('*')):
                if source.is_file():
                    entry = zipfile.ZipInfo(source.relative_to(compiled).as_posix())
                    entry.create_system = 3
                    entry.external_attr = 0o100644 << 16
                    archive.writestr(entry, source.read_bytes())
        if output_directory is not None:
            shutil.copyfile(
                compiled / 'manifest.json', output_directory / 'manifest.json'
            )
        if directory is not None:
            shutil.copytree(compiled, directory, dirs_exist_ok=True)
            (directory / 'package.json').write_text('{"type":"module"}\n')


def main():
    parser = argparse.ArgumentParser()
    outputs = parser.add_mutually_exclusive_group(required=True)
    outputs.add_argument('--output', type=Path)
    outputs.add_argument('--output-directory', type=Path)
    parser.add_argument('--version')
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--source-root', type=Path, default=EXTENSION_ROOT)
    arguments = parser.parse_args()
    try:
        build(
            arguments.output,
            arguments.version,
            arguments.directory,
            arguments.output_directory,
            arguments.source_root.resolve(),
        )
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'FAIL: Could not build the extension: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
