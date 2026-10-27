import os
import re
import stat
from urllib.parse import urlsplit

ENDPOINT_MESSAGE = 'Connector endpoint must be a ws/wss URL without credentials, query, or fragment.'


def validate_endpoint(endpoint):
    try:
        parsed = urlsplit(endpoint)
        port = parsed.port
    except ValueError:
        raise ValueError(ENDPOINT_MESSAGE) from None
    if (
        len(endpoint) > 2048
        or any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in endpoint)
        or parsed.scheme not in ('ws', 'wss')
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or '?' in endpoint
        or '#' in endpoint
        or port == 0
    ):
        raise ValueError(ENDPOINT_MESSAGE)


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
        raise ValueError('Connector token must contain 64 lowercase hexadecimal characters.')
    return token_bytes.rstrip(b'\n').decode('ascii')


def managed_settings(environment):
    endpoint = environment.get('RAICHO_CONNECTOR_ENDPOINT', '')
    token_path = environment.get('RAICHO_CONNECTOR_TOKEN_FILE', '')
    if not endpoint and not token_path:
        return None
    if not endpoint or not token_path:
        raise ValueError('Connector endpoint and token file must be configured together.')
    validate_endpoint(endpoint)
    return {'endpoint': endpoint, 'token': read_token(token_path)}
