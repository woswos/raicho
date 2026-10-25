import argparse
import os
import secrets
import sys
from pathlib import Path

from runtime.credentials.raicho_connector_file_checks import (
    FILENAMES,
    SERVICE_UID,
    STAGING,
    discard_staging,
    validate_metadata,
    validate_token,
)

TOKEN_BYTES = 32
OPERATIONS = ('init', 'rotate', 'reactivate', 'publish', 'finish', 'check')


def prepare(directory, owner_uid, owner_gid):
    descriptor = os.open(
        STAGING,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
        dir_fd=directory,
    )
    try:
        with os.fdopen(descriptor, 'wb') as output:
            os.fchmod(output.fileno(), 0o600)
            os.fchown(output.fileno(), owner_uid, owner_gid)
            output.write((secrets.token_hex(TOKEN_BYTES) + '\n').encode('ascii'))
            output.flush()
            os.fsync(output.fileno())
        replace(directory, STAGING, 'connector.pending')
    finally:
        try:
            os.unlink(STAGING, dir_fd=directory)
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
        raise ValueError('Connector rotation requires the existing token')
    if pending:
        return 'pending'
    return prepare(directory, owner_uid, owner_gid)


def update_operation(operation, directory, present):
    current, pending, previous = present
    if operation == 'publish':
        if not pending or previous:
            raise ValueError('Publishing requires a pending token without a backup')
        if current:
            replace(directory, 'connector.token', 'connector.previous')
        replace(directory, 'connector.pending', 'connector.token')
    else:
        if not current or pending or (operation == 'check' and previous):
            raise ValueError('Connector token files need recovery before use')
        if previous:
            os.unlink('connector.previous', dir_fd=directory)
            os.fsync(directory)
    return 'current'


def operate(operation, path, owner_uid=SERVICE_UID, owner_gid=SERVICE_UID):
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
        filenames = discard_staging(directory, filenames)
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
    parser = argparse.ArgumentParser(description='Manage private connector token files')
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
            'FAIL: Cannot securely access or update connector token files',
            file=sys.stderr,
        )
        return 1
    print(result)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
