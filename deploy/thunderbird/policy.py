import json
import os
import re
import tempfile
from pathlib import Path

from .managed_settings import managed_settings

EXTENSION_ID = 'connector@raicho'


def extension_archive(extension_directory):
    try:
        manifest = json.loads((extension_directory / 'manifest.json').read_text())
        version = manifest['version']
        identifier = manifest['browser_specific_settings']['gecko']['id']
    except (OSError, ValueError, KeyError, TypeError):
        raise ValueError('Packaged extension metadata is invalid.') from None
    if (
        identifier != EXTENSION_ID
        or not isinstance(version, str)
        or not re.fullmatch(r'[0-9]{1,5}(?:\.[0-9]{1,5}){2}', version)
        or any(int(component) > 65535 for component in version.split('.'))
    ):
        raise ValueError('Packaged extension metadata is invalid.')
    archive = extension_directory / f'raicho-{version}.xpi'
    if not archive.is_file():
        raise ValueError('Packaged extension archive is missing.')
    return archive


def write_policies(runtime_directory, extension_directory, environment):
    policies = {
        'DisableAppUpdate': True,
        'ExtensionSettings': {
            EXTENSION_ID: {
                'installation_mode': 'force_installed',
                'install_url': extension_archive(extension_directory).as_uri(),
                'updates_disabled': True,
            }
        },
    }
    settings = managed_settings(environment)
    if settings is not None:
        policies['3rdparty'] = {'Extensions': {EXTENSION_ID: settings}}
    if runtime_directory.is_symlink():
        raise ValueError('Runtime directory must not be a symbolic link.')
    runtime_directory.mkdir(mode=0o700, exist_ok=True)
    if runtime_directory.stat().st_uid != os.geteuid():
        raise ValueError('Runtime directory must be owned by the current user.')
    runtime_directory.chmod(0o700)
    destination = runtime_directory / 'policies.json'
    descriptor, temporary_name = tempfile.mkstemp(prefix='.policies-', dir=runtime_directory)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, 'w') as policy_file:
            os.fchmod(policy_file.fileno(), 0o600)
            json.dump({'policies': policies}, policy_file)
            policy_file.write('\n')
            policy_file.flush()
            os.fsync(policy_file.fileno())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination
