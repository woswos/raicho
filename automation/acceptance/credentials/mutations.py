import os
import secrets
from pathlib import Path

FIXTURE = Path('/fixture')
CREDENTIALS = FIXTURE / 'credentials'
CURRENT = CREDENTIALS / 'connector.token'
SERVICE_UID = 10001
OTHER_UID = 10002


def mutation(arguments):
    action = arguments.action
    preserved = FIXTURE / 'preserved.token'
    if action in ('hide', 'mismatch'):
        assert not preserved.exists(), 'A fixture token is already preserved'
        CURRENT.rename(preserved)
        if action == 'mismatch':
            descriptor = os.open(CURRENT, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, 'w') as token_file:
                token_file.write(secrets.token_hex(32) + '\n')
            os.chown(CURRENT, SERVICE_UID, SERVICE_UID)
    elif action == 'restore':
        assert preserved.is_file(), 'Preserved fixture token is missing'
        preserved.replace(CURRENT)
    elif action == 'unsafe_mode':
        CURRENT.chmod(0o644)
    elif action == 'safe_mode':
        CURRENT.chmod(0o600)
    elif action == 'unsafe_owner':
        os.chown(CURRENT, OTHER_UID, OTHER_UID)
    elif action == 'safe_owner':
        os.chown(CURRENT, SERVICE_UID, SERVICE_UID)
    elif action == 'mid_publish':
        assert not (CREDENTIALS / 'connector.previous').exists()
        CURRENT.rename(CREDENTIALS / 'connector.previous')
    elif action == 'cleanup':
        clean_directory(CREDENTIALS)
        for archive in FIXTURE.glob('revoked.*'):
            clean_directory(archive)
        preserved.unlink(missing_ok=True)


def clean_directory(directory):
    if not directory.exists():
        assert not directory.is_symlink()
        return
    assert directory.is_dir() and not directory.is_symlink()
    for path in directory.iterdir():
        assert path.is_file() and not path.is_symlink()
        path.unlink()
    directory.rmdir()
