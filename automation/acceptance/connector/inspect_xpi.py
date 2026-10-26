import json
import zipfile
from pathlib import Path


def inspect_archive(path, token):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        manifest = json.loads(archive.read('manifest.json'))
        assert manifest['manifest_version'] == 2
        assert (
            manifest['browser_specific_settings']['gecko']['id'] == 'connector@raicho'
        )
        assert manifest['permissions'] == ['storage'], (
            'Production gained mail permissions'
        )
        assert not manifest.get('optional_permissions')
        assert not manifest.get('experiment_apis')
        assert 'extension/src/connector_transport.js' in names, (
            'Production transport is missing'
        )
        for name in names:
            assert not name.endswith(('.ts', '.map')), (
                'Source/test artifact entered XPI'
            )
            contents = archive.read(name)
            assert all(
                marker not in contents
                for marker in (
                    token,
                    b'mail_probe',
                    b'fixture@raicho.test',
                )
            ), 'Production XPI contains secret or probe content'
    print(
        f'Production XPI {manifest["version"]}: storage permission only, no secret/probe code'
    )


if __name__ == '__main__':
    directory = Path('/opt/raicho/extension')
    manifest = json.loads((directory / 'manifest.json').read_text())
    token = Path('/run/secrets/raicho_connector_token').read_bytes().strip()
    assert len(token) == 64, 'Fixture credential is invalid'
    inspect_archive(directory / f'raicho-{manifest["version"]}.xpi', token)
