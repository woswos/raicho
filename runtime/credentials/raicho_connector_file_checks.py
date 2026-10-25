import os
import re
import stat

FILENAMES = {'connector.token', 'connector.pending', 'connector.previous'}
STAGING = '.connector.preparing'
SERVICE_UID = 10001
TOKEN_HEX_LENGTH = 64


def validate_metadata(metadata, owner_uid, owner_gid, mode):
    if (
        metadata.st_uid != owner_uid
        or metadata.st_gid != owner_gid
        or stat.S_IMODE(metadata.st_mode) != mode
    ):
        raise ValueError(
            'Connector files require the configured owner and private modes'
        )


def validate_token(directory, filename, owner_uid, owner_gid):
    descriptor = os.open(
        filename, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory
    )
    with os.fdopen(descriptor, 'rb') as source:
        metadata = os.fstat(source.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ValueError('Connector tokens must be regular files without links')
        validate_metadata(metadata, owner_uid, owner_gid, 0o600)
        contents = source.read(TOKEN_HEX_LENGTH + 2)
        if not re.fullmatch(rb'[0-9a-f]{%d}\n?' % TOKEN_HEX_LENGTH, contents):
            raise ValueError('Connector token has an invalid format')


def discard_staging(directory, filenames):
    if STAGING not in filenames:
        return filenames
    metadata = os.stat(STAGING, dir_fd=directory, follow_symlinks=False)
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise ValueError('Connector staging must be a regular file without links')
    os.unlink(STAGING, dir_fd=directory)
    os.fsync(directory)
    return filenames - {STAGING}
