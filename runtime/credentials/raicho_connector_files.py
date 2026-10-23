import argparse
import os
import re
import secrets
import stat
import sys
from pathlib import Path

FILENAMES = {'connector.token', 'connector.pending', 'connector.previous'}
OPERATIONS = ('init', 'rotate', 'reactivate', 'publish', 'finish', 'check')


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
            raise ValueError('Connector secrets must be regular files without links')
        validate_metadata(metadata, owner_uid, owner_gid, 0o600)
        if not re.fullmatch(rb'[0-9a-f]{64}\n?', source.read(66)):
            raise ValueError('Connector secret has an invalid format')


def prepare(directory, owner_uid, owner_gid):
    staging = '.connector.preparing'
    descriptor = os.open(
        staging,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
        dir_fd=directory,
    )
    try:
        with os.fdopen(descriptor, 'wb') as output:
            os.fchmod(output.fileno(), 0o600)
            os.fchown(output.fileno(), owner_uid, owner_gid)
            output.write((secrets.token_hex(32) + '\n').encode('ascii'))
            output.flush()
            os.fsync(output.fileno())
        replace(directory, staging, 'connector.pending')
    finally:
        try:
            os.unlink(staging, dir_fd=directory)
            os.fsync(directory)
        except FileNotFoundError:
            pass
    return 'pending'


def replace(directory, source, destination):
    os.replace(source, destination, src_dir_fd=directory, dst_dir_fd=directory)
    os.fsync(directory)


def prepare_operation(operation, directory, present, owner_uid, owner_gid):
    current, pending, previous = present
    if operation == 'init':
        if previous or (current and pending):
            raise ValueError('Initialization cannot recover a rotation')
        if current:
            return 'current'
    elif operation == 'reactivate' and current and not pending and not previous:
        return 'current'
    elif previous:
        if current and not pending:
            return 'current'
        if pending and not current:
            replace(directory, 'connector.previous', 'connector.token')
            return 'pending'
        raise ValueError('Connector rotation files are inconsistent')
    elif not current and operation == 'rotate':
        raise ValueError('Connector rotation requires the existing secret')
    if pending:
        return 'pending'
    return prepare(directory, owner_uid, owner_gid)


def update_operation(operation, directory, present):
    current, pending, previous = present
    if operation == 'publish':
        if not pending or previous:
            raise ValueError('Publishing requires a pending secret without a backup')
        if current:
            replace(directory, 'connector.token', 'connector.previous')
        replace(directory, 'connector.pending', 'connector.token')
    else:
        if not current or pending or (operation == 'check' and previous):
            raise ValueError('Connector secret files need recovery before use')
        if previous:
            os.unlink('connector.previous', dir_fd=directory)
            os.fsync(directory)
    return 'current'


def operate(operation, path, owner_uid=10001, owner_gid=10001):
    if operation not in OPERATIONS:
        raise ValueError('Unknown connector file operation')
    directory = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        filenames = set(os.listdir(directory))
        if not filenames and operation in ('init', 'reactivate'):
            os.fchmod(directory, 0o700)
            os.fchown(directory, owner_uid, owner_gid)
            os.fsync(directory)
        validate_metadata(os.fstat(directory), owner_uid, owner_gid, 0o700)
        if filenames - FILENAMES:
            raise ValueError('Connector directory contains unexpected files')
        for filename in filenames:
            validate_token(directory, filename, owner_uid, owner_gid)
        present = tuple(
            filename in filenames
            for filename in (
                'connector.token',
                'connector.pending',
                'connector.previous',
            )
        )
        if operation in ('init', 'rotate', 'reactivate'):
            return prepare_operation(
                operation, directory, present, owner_uid, owner_gid
            )
        return update_operation(operation, directory, present)
    finally:
        os.close(directory)


def main(arguments=None):
    parser = argparse.ArgumentParser(
        description='Manage private connector secret files'
    )
    parser.add_argument('operation', choices=OPERATIONS)
    parser.add_argument('directory', type=Path)
    options = parser.parse_args(arguments)
    try:
        result = operate(options.operation, options.directory)
    except ValueError as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    except OSError:
        print(
            'FAIL: Cannot securely access or update connector secret files',
            file=sys.stderr,
        )
        return 1
    print(result)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
