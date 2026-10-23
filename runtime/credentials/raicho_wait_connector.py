import json
import sys
import time
import urllib.request


def wait_for_connector(
    timeout=90, request=urllib.request.urlopen, pause=time.sleep, clock=time.monotonic
):
    deadline = clock() + timeout
    while (remaining := deadline - clock()) > 0:
        try:
            with request(
                'http://raicho:8080/api/status', timeout=min(5, remaining)
            ) as response:
                payload = json.loads(response.read(65537))
        except (OSError, ValueError):
            payload = None
        if isinstance(payload, dict) and isinstance(payload.get('backend'), dict):
            backend = payload['backend']
            if backend.get('kind') == 'thunderbird':
                if backend.get('status') in ('revoked', 'unconfigured'):
                    raise ValueError('Connector credential is not active')
                heartbeats = backend.get('heartbeat_count')
                if (
                    payload.get('status') == 'ready'
                    and backend.get('status') == 'connected'
                    and type(heartbeats) is int
                    and heartbeats > 0
                ):
                    return
        pause(min(1, remaining))
    raise ValueError(
        'Thunderbird did not establish an authenticated connection in time'
    )


def main():
    try:
        wait_for_connector()
    except ValueError as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    print('Authenticated Thunderbird connection and heartbeat verified')
    return 0


if __name__ == '__main__':
    sys.exit(main())
