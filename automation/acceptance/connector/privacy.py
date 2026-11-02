import argparse
import sqlite3
import sys
import urllib.request
from contextlib import closing
from pathlib import Path

from automation.acceptance.connector.endpoints import STATUS_URL
from automation.acceptance.credentials.files import read_token, stored_files

APPLICATION_TABLES = {'_sqlx_migrations', 'connector_credentials', 'login_password', 'browser_sessions', 'preferences'}
MAIL_CANARIES = (
    b'raicho-private-subject-acceptance',
    b'raicho-private-body-acceptance',
    b'private-sender-acceptance@raicho.test',
)


def check_payload(contents, token):
    assert all(marker not in contents for marker in (token, *MAIL_CANARIES)), 'Private data was retained'


def check_database(directory, token):
    with closing(sqlite3.connect(f'file:{directory}/raicho.sqlite3?mode=ro', uri=True)) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert tables <= APPLICATION_TABLES, 'Unexpected application table'
        check_payload('\n'.join(connection.iterdump()).encode(), token)
    for contents in stored_files(directory):
        check_payload(contents, token)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('logs', 'database', 'diagnostics'))
    arguments = parser.parse_args()
    fixture_token = read_token(Path('/fixture/credentials/connector.token'))
    if arguments.mode == 'logs':
        check_payload(sys.stdin.buffer.read(), fixture_token)
    elif arguments.mode == 'database':
        check_database(Path('/database'), fixture_token)
    else:
        with urllib.request.urlopen(STATUS_URL, timeout=5) as response:
            contents = response.read(65537)
        assert len(contents) <= 65536, 'Diagnostics exceeded the fixture bound'
        check_payload(contents, fixture_token)
    print(f'Privacy passed: {arguments.mode} retained neither raw token nor mail canaries')


if __name__ == '__main__':
    main()
