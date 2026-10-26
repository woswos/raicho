import argparse
import hashlib
import hmac
import json
import re
import sqlite3
import stat
import sys
from pathlib import Path

from automation.acceptance.credentials.mutations import (
    CREDENTIALS,
    CURRENT,
    SERVICE_UID,
    mutation,
)

DATABASE_DIRECTORY = Path('/database')


def token(path):
    metadata = path.stat(follow_symlinks=False)
    assert stat.S_ISREG(metadata.st_mode), 'Token must be a regular file'
    assert metadata.st_uid == SERVICE_UID, 'Token must belong to the service UID'
    assert stat.S_IMODE(metadata.st_mode) == 0o600, 'Token must use mode 0600'
    contents = path.read_bytes()
    assert re.fullmatch(rb'[0-9a-f]{64}\n?', contents), 'Token is not canonical'
    return contents.rstrip(b'\n')


def database_check(arguments):
    metadata = CREDENTIALS.stat(follow_symlinks=False)
    assert stat.S_ISDIR(metadata.st_mode), 'Token directory must be real'
    assert metadata.st_uid == SERVICE_UID, 'Token directory must belong to the service UID'
    assert stat.S_IMODE(metadata.st_mode) == 0o700, 'Token directory mode differs'
    selected = token(CREDENTIALS / arguments.token)
    with sqlite3.connect(f'file:{DATABASE_DIRECTORY}/raicho.sqlite3?mode=ro', uri=True) as connection:
        rows = connection.execute(
            'SELECT backend_kind, stored_key, server_key, revoked, revision FROM connector_credentials'
        ).fetchall()
        assert connection.execute('PRAGMA integrity_check').fetchone() == ('ok',)
    assert len(rows) == 1, 'Exactly one connector credential must exist'
    backend, stored_key, server_key, revoked, revision = rows[0]
    assert backend == 'thunderbird', 'Unexpected persisted backend kind'
    client_key = hmac.digest(selected, b'raicho connector client key', 'sha256')
    assert stored_key == hashlib.sha256(client_key).digest(), 'Token and stored key differ'
    assert server_key == hmac.digest(selected, b'raicho connector server key', 'sha256'), 'Token and server key differ'
    assert revoked == int(arguments.revoked), 'Persisted revocation state differs'
    assert revision == arguments.revision, 'Credential revision differs'
    for path in DATABASE_DIRECTORY.iterdir():
        if path.is_file():
            assert selected not in path.read_bytes(), 'Database leaked the raw token'
    print('Credential keys, permissions, persistence, and token isolation passed')


def mount_check():
    server, thunderbird = json.load(sys.stdin)
    assert server['Config']['User'] == f'{SERVICE_UID}:{SERVICE_UID}', 'Server UID differs'
    assert all(mount['Type'] != 'bind' for mount in server['Mounts']), 'Ordinary server gained a host mount'
    assert all(
        'credential' not in mount['Destination']
        and 'secret' not in mount['Destination']
        and 'thunderbird' not in mount.get('Name', '')
        for mount in server['Mounts']
    ), 'Ordinary server gained credential or profile access'
    token_mounts = [mount for mount in thunderbird['Mounts'] if mount['Type'] == 'bind']
    assert len(token_mounts) == 1, 'Thunderbird must receive only its token bind'
    assert not token_mounts[0]['RW'], 'Thunderbird token must be read-only'
    assert token_mounts[0]['Source'].endswith('/credentials/connector.token')
    assert all(
        not re.search(r'[0-9a-f]{64}', variable)
        for container in (server, thunderbird)
        for variable in container['Config']['Env']
    ), 'Container environment contains a raw token'
    print('Ordinary server has no token/profile mount and Thunderbird token is read-only')


def log_check():
    assert token(CURRENT) not in sys.stdin.buffer.read(), 'Service logs leaked the raw token'
    print('Service logs contain no raw token')


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
