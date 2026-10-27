import argparse
import json
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path

DATABASE = Path('/fixture/raicho/raicho.sqlite3')
PROFILE = Path('/fixture/thunderbird/profile')
FIXTURE_VALUE = 'stage-one-persistence'


def response(path, expected=200):
    try:
        result = urllib.request.urlopen(f'http://raicho:8080{path}', timeout=5)
    except urllib.error.HTTPError as error:
        result = error
    with result:
        if result.status != expected:
            raise AssertionError(f'{path}: expected {expected}, got {result.status}')
        return result.headers, result.read()


def check_http():
    for endpoint in ('/health/live', '/health/ready', '/api/status'):
        headers, body = response(endpoint)
        if headers.get('Cache-Control') != 'no-store':
            raise AssertionError(f'{endpoint}: missing no-store')
        payload = json.loads(body)
        if endpoint == '/api/status':
            assert payload['status'] == 'ready'
            assert payload['backend'] == {
                'status': 'unconfigured',
                'kind': 'thunderbird',
                'generation': None,
                'last_error': None,
                'heartbeat_count': 0,
            }
            assert payload['database']['engine'] == 'sqlite'
            assert payload['database']['version'] == '3.51.3'
            if not isinstance(payload.get('version'), str) or not payload['version']:
                raise AssertionError('/api/status: missing product version')
            if not isinstance(payload.get('commit'), str) or not payload['commit']:
                raise AssertionError('/api/status: missing build commit')
    headers, body = response('/')
    assert 'text/html' in headers['Content-Type']
    assert b'Raicho' in body
    for asset in ('/main.js', '/assets/brand/logos/horizontal.svg'):
        response(asset)
    response('/missing-asset.js', 404)
    response('/api/missing', 404)
    response('/connector/v1', 404)
    response('/../Cargo.toml', 404)
    response('/.git/config', 404)
    print('HTTP diagnostics, cache headers, assets, and route isolation passed')


def seed():
    if not DATABASE.is_file() or not (PROFILE / 'prefs.js').is_file():
        raise AssertionError('Start and stop both services before seeding fixtures.')
    with sqlite3.connect(DATABASE) as connection:
        connection.execute('CREATE TABLE raicho_fixture (value TEXT NOT NULL)')
        connection.execute('INSERT INTO raicho_fixture VALUES (?)', (FIXTURE_VALUE,))
    with (PROFILE / 'prefs.js').open('a') as preferences:
        preferences.write(f'\nuser_pref("raicho.stage1.fixture", "{FIXTURE_VALUE}");\n')
    print('Seeded persistence fixtures in the stopped disposable deployment')


def check_persistence():
    with sqlite3.connect(f'file:{DATABASE}?mode=ro', uri=True) as connection:
        assert connection.execute('SELECT value FROM raicho_fixture').fetchall() == [(FIXTURE_VALUE,)]
        assert connection.execute('PRAGMA integrity_check').fetchone() == ('ok',)
    assert FIXTURE_VALUE in (PROFILE / 'prefs.js').read_text()
    print('SQLite contents and actual Thunderbird preferences survived recreation')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('http', 'seed', 'persistence'))
    mode = parser.parse_args().mode
    {'http': check_http, 'seed': seed, 'persistence': check_persistence}[mode]()


if __name__ == '__main__':
    main()
