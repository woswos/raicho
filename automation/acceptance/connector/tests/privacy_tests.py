import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from automation.acceptance.connector.privacy import (
    MAIL_CANARIES,
    check_database,
    check_payload,
)


class ConnectorPrivacyTests(unittest.TestCase):
    def test_rejects_raw_token_and_all_mail_markers_without_echoing_them(self):
        token = b'private-fixture-token'
        for marker in (token, *MAIL_CANARIES):
            with self.assertRaisesRegex(AssertionError, '^Private data was retained$'):
                check_payload(b'prefix' + marker + b'suffix', token)
        check_payload(b'connected; authentication_failed', token)

    def test_database_schema_cannot_gain_a_mail_store(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with (
                closing(sqlite3.connect(directory / 'raicho.sqlite3')) as connection,
                connection,
            ):
                connection.execute('CREATE TABLE _sqlx_migrations (version INTEGER)')
                connection.execute('CREATE TABLE connector_credentials (digest BLOB)')
            check_database(directory, b'private-fixture-token')
            with (
                closing(sqlite3.connect(directory / 'raicho.sqlite3')) as connection,
                connection,
            ):
                connection.execute('CREATE TABLE messages (body TEXT)')
            with self.assertRaisesRegex(AssertionError, 'Unexpected application table'):
                check_database(directory, b'private-fixture-token')

    def test_database_sidecars_are_scanned_as_well_as_live_rows(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with (
                closing(sqlite3.connect(directory / 'raicho.sqlite3')) as connection,
                connection,
            ):
                connection.execute('CREATE TABLE connector_credentials (digest BLOB)')
            (directory / 'retained-sidecar').write_bytes(MAIL_CANARIES[0])
            with self.assertRaisesRegex(AssertionError, 'Private data was retained'):
                check_database(directory, b'private-fixture-token')
