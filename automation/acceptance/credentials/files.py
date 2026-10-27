import re
import stat

from automation.acceptance.credentials.mutations import SERVICE_UID


def read_token(path):
    metadata = path.stat(follow_symlinks=False)
    assert stat.S_ISREG(metadata.st_mode), 'Token must be a regular file'
    assert metadata.st_uid == SERVICE_UID, 'Token must belong to the service UID'
    assert stat.S_IMODE(metadata.st_mode) == 0o600, 'Token must use mode 0600'
    contents = path.read_bytes()
    assert re.fullmatch(rb'[0-9a-f]{64}\n?', contents), 'Token is not canonical'
    return contents.rstrip(b'\n')


def stored_files(directory):
    for path in directory.iterdir():
        if path.is_file():
            yield path.read_bytes()
