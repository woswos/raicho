import json
import zipfile
from pathlib import Path


def inspect_archive(path, token):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        manifest = json.loads(archive.read('manifest.json'))
        assert manifest['manifest_version'] == 2
        assert manifest['browser_specific_settings']['gecko']['id'] == 'connector@raicho'
        assert manifest['permissions'] == ['storage', 'accountsRead', 'messagesRead'], 'Production permissions changed'
        assert not manifest.get('optional_permissions')
        assert not manifest.get('experiment_apis')
        assert 'extension/src/connector_transport.js' in names, 'Production transport is missing'
        for name in names:
            assert not name.endswith(('.ts', '.map')), 'Source/test artifact entered XPI'
            contents = archive.read(name)
            assert all(
                marker not in contents
                for marker in (
                    token,
                    b'mail_probe',
                    b'fixture@raicho.test',
                )
            ), 'Production XPI contains secret or probe content'
    print(f'Production XPI {manifest["version"]}: storage and read-only mail permissions, no secret/probe code')


if __name__ == '__main__':
    (archive,) = Path('/opt/raicho/extension').glob('raicho-*.xpi')
    token = Path('/run/secrets/raicho_connector_token').read_bytes().strip()
    assert len(token) == 64, 'Fixture credential is invalid'
    inspect_archive(archive, token)
