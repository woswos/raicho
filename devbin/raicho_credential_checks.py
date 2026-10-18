import argparse
import hashlib
import json
import os
import re
import secrets
import sqlite3
import stat
import sys
from pathlib import Path

FIXTURE = Path('/fixture')
CREDENTIALS = FIXTURE / 'credentials'
DATABASE_DIRECTORY = Path('/database')
CURRENT = CREDENTIALS / 'connector.token'


def token(path):
    metadata = path.stat(follow_symlinks=False)
    assert stat.S_ISREG(metadata.st_mode), 'Credential must be a regular file'
    assert metadata.st_uid == 10001, 'Credential must belong to UID 10001'
    assert stat.S_IMODE(metadata.st_mode) == 0o600, 'Credential must use mode 0600'
    contents = path.read_bytes()
    assert re.fullmatch(rb'[0-9a-f]{64}\n?', contents), 'Credential is not canonical'
    return contents.rstrip(b'\n')


def database_check(arguments):
    metadata = CREDENTIALS.stat(follow_symlinks=False)
    assert stat.S_ISDIR(metadata.st_mode), 'Credential directory must be real'
    assert metadata.st_uid == 10001, 'Credential directory must belong to UID 10001'
    assert stat.S_IMODE(metadata.st_mode) == 0o700, 'Credential directory mode differs'
    selected = token(CREDENTIALS / arguments.token)
    with sqlite3.connect(
        f'file:{DATABASE_DIRECTORY}/raicho.sqlite3?mode=ro', uri=True
    ) as connection:
        rows = connection.execute(
            'SELECT backend_kind, token_digest, revoked, revision '
            'FROM connector_credentials'
        ).fetchall()
        assert connection.execute('PRAGMA integrity_check').fetchone() == ('ok',)
    assert len(rows) == 1, 'Exactly one connector credential must exist'
    backend, digest, revoked, revision = rows[0]
    assert backend == 'thunderbird', 'Unexpected persisted backend kind'
    assert digest == hashlib.sha256(selected).digest(), 'File and digest differ'
    assert revoked == int(arguments.revoked), 'Persisted revocation state differs'
    assert revision == arguments.revision, 'Credential revision differs'
    for path in DATABASE_DIRECTORY.iterdir():
        if path.is_file():
            assert selected not in path.read_bytes(), 'Database leaked raw credential'
    print('Credential digest, permissions, persistence, and token isolation passed')


def mutation(arguments):
    action = arguments.action
    preserved = FIXTURE / 'preserved.token'
    if action in ('hide', 'mismatch'):
        assert not preserved.exists(), 'A fixture token is already preserved'
        CURRENT.rename(preserved)
        if action == 'mismatch':
            descriptor = os.open(CURRENT, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, 'w') as secret_file:
                secret_file.write(secrets.token_hex(32) + '\n')
            os.chown(CURRENT, 10001, 10001)
    elif action == 'restore':
        assert preserved.is_file(), 'Preserved fixture credential is missing'
        preserved.replace(CURRENT)
    elif action == 'unsafe_mode':
        CURRENT.chmod(0o644)
    elif action == 'safe_mode':
        CURRENT.chmod(0o600)
    elif action == 'unsafe_owner':
        os.chown(CURRENT, 10002, 10002)
    elif action == 'safe_owner':
        os.chown(CURRENT, 10001, 10001)
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


def mount_check():
    server, thunderbird = json.load(sys.stdin)
    assert server['Config']['User'] == '10001:10001', 'Server UID differs'
    assert all(mount['Type'] != 'bind' for mount in server['Mounts']), (
        'Ordinary server gained a host mount'
    )
    assert all(
        'credential' not in mount['Destination']
        and 'secret' not in mount['Destination']
        and 'thunderbird' not in mount.get('Name', '')
        for mount in server['Mounts']
    ), 'Ordinary server gained credential or profile access'
    secrets_mounted = [
        mount for mount in thunderbird['Mounts'] if mount['Type'] == 'bind'
    ]
    assert len(secrets_mounted) == 1, 'Thunderbird must receive only its token bind'
    assert not secrets_mounted[0]['RW'], 'Thunderbird token must be read-only'
    assert secrets_mounted[0]['Source'].endswith('/credentials/connector.token')
    assert all(
        not re.search(r'[0-9a-f]{64}', variable)
        for container in (server, thunderbird)
        for variable in container['Config']['Env']
    ), 'Container environment contains a raw credential'
    print(
        'Ordinary server has no secret/profile mount and Thunderbird secret is read-only'
    )


def log_check():
    assert token(CURRENT) not in sys.stdin.buffer.read(), (
        'Service logs leaked credential'
    )
    print('Service logs contain no raw credential')


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    database = commands.add_parser('database')
    database.add_argument('--token', default='connector.token')
    database.add_argument('--revision', type=int, required=True)
    database.add_argument('--revoked', action='store_true')
    mutate = commands.add_parser('mutate')
    mutate.add_argument('action')
    commands.add_parser('mounts')
    commands.add_parser('logs')
    arguments = parser.parse_args()
    if arguments.command == 'database':
        database_check(arguments)
    elif arguments.command == 'mutate':
        mutation(arguments)
    elif arguments.command == 'mounts':
        mount_check()
    else:
        log_check()


if __name__ == '__main__':
    main()
