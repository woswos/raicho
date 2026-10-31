import json
import re
import time
import urllib.error
import urllib.request

from automation.acceptance.connector.endpoints import STATUS_URL
from automation.paths import REPOSITORY_ROOT


def contract():
    return json.loads((REPOSITORY_ROOT / 'protocol/schema/status.schema.json').read_text())


def status():
    with urllib.request.urlopen(STATUS_URL, timeout=5) as response:
        assert response.headers.get('Cache-Control') == 'no-store'
        payload = json.load(response)
    schema = contract()
    assert set(payload) == set(schema['properties'])
    assert payload['status'] == 'ready'
    backend = payload['backend']
    assert backend['kind'] == 'thunderbird'
    assert set(backend) == set(schema['definitions']['BackendStatus']['properties'])
    return backend


def wait_for_status(arguments):
    deadline = time.monotonic() + arguments.timeout
    failure = None
    while time.monotonic() < deadline:
        try:
            backend = status()
            if backend['status'] == arguments.status:
                generation = backend['generation']
                if arguments.status == 'connected':
                    assert re.fullmatch(r'[a-f0-9]{32}', generation)
                    if generation == arguments.previous_generation:
                        time.sleep(1)
                        continue
                    if backend['heartbeat_count'] < arguments.minimum_heartbeats:
                        time.sleep(1)
                        continue
                else:
                    assert generation is None
                print(generation or arguments.status)
                return
        except (OSError, ValueError, urllib.error.URLError) as error:
            failure = error
        time.sleep(1)
    raise AssertionError(f'Connector did not become {arguments.status} in time') from failure


def snapshot():
    backend = status()
    definitions = contract()['definitions']
    assert backend['status'] in definitions['BackendState']['enum']
    assert backend['last_error'] in [None, *definitions['BackendError']['enum']]
    assert type(backend['heartbeat_count']) is int
    print(
        json.dumps(
            {
                'status': backend['status'],
                'last_error': backend['last_error'],
                'heartbeat_count': backend['heartbeat_count'],
                'has_generation': backend['generation'] is not None,
            }
        )
    )
