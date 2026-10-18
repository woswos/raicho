import json
import os
import re
import stat
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

EXTENSION_ID = 'connector@raicho'


def extension_archive(extension_directory):
    try:
        manifest = json.loads((extension_directory / 'manifest.json').read_text())
        version = manifest['version']
        identifier = manifest['browser_specific_settings']['gecko']['id']
        if (
            identifier != EXTENSION_ID
            or not isinstance(version, str)
            or not re.fullmatch(r'[0-9]{1,5}(?:\.[0-9]{1,5}){2}', version)
            or any(int(component) > 65535 for component in version.split('.'))
        ):
            raise ValueError
    except (OSError, ValueError, KeyError, TypeError):
        raise ValueError('Packaged extension metadata is invalid.') from None
    archive = extension_directory / f'raicho-{version}.xpi'
    if not archive.is_file():
        raise ValueError('Packaged extension archive is missing.')
    return archive


def validate_endpoint(endpoint):
    try:
        parsed = urlsplit(endpoint)
        if (
            len(endpoint) > 2048
            or any(
                character.isspace() or ord(character) < 32 or ord(character) == 127
                for character in endpoint
            )
            or parsed.scheme not in ('ws', 'wss')
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or '?' in endpoint
            or '#' in endpoint
            or parsed.port == 0
        ):
            raise ValueError
    except ValueError:
        raise ValueError(
            'Connector endpoint must be a ws/wss URL without credentials, query, or fragment.'
        ) from None


def read_token(token_path):
    try:
        descriptor = os.open(token_path, os.O_RDONLY | os.O_NONBLOCK)
        with os.fdopen(descriptor, 'rb') as token_file:
            if not stat.S_ISREG(os.fstat(token_file.fileno()).st_mode):
                raise ValueError('Connector token file must be a regular file.')
            token_bytes = token_file.read(66)
    except OSError:
        raise ValueError('Connector token file could not be read.') from None
    if not re.fullmatch(rb'[0-9a-f]{64}\n?', token_bytes):
        raise ValueError(
            'Connector token must contain 64 lowercase hexadecimal characters.'
        )
    return token_bytes.rstrip(b'\n').decode('ascii')


def managed_settings(environment):
    endpoint = environment.get('RAICHO_CONNECTOR_ENDPOINT', '')
    token_path = environment.get('RAICHO_CONNECTOR_TOKEN_FILE', '')
    if not endpoint and not token_path:
        return None
    if not endpoint or not token_path:
        raise ValueError(
            'Connector endpoint and token file must be configured together.'
        )
    validate_endpoint(endpoint)
    return {'endpoint': endpoint, 'token': read_token(token_path)}


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
    descriptor, temporary_name = tempfile.mkstemp(
        prefix='.policies-', dir=runtime_directory
    )
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
