import argparse
import socket
import urllib.error
import urllib.request

from automation.acceptance.connector.deployment import deployment
from automation.acceptance.connector.endpoints import GATEWAY_ADDRESS, RAICHO_URL, upgrade_request
from automation.acceptance.connector.idle import observe_idle
from automation.acceptance.connector.status import (
    snapshot,
    wait_for_status,
)


def raw_request(request_line):
    with socket.create_connection(GATEWAY_ADDRESS, timeout=5) as connection:
        connection.sendall(upgrade_request(request_line, 'attacker.invalid', 'dGhlIHNhbXBsZSBub25jZQ=='))
        response = connection.recv(1024).split(b'\r\n', 1)[0]
    return int(response.split()[1])


def gateway_routes():
    for request_line in (
        'GET / HTTP/1.1',
        'GET /health/live HTTP/1.1',
        'GET /connector/v1/ HTTP/1.1',
        'GET /connector/v1?destination=thunderbird:6080 HTTP/1.1',
        'GET /connector/%76%31 HTTP/1.1',
        'GET http://thunderbird:6080/connector/v1 HTTP/1.1',
        'POST /connector/v1 HTTP/1.1',
        'CONNECT thunderbird:6080 HTTP/1.1',
    ):
        assert raw_request(request_line) in (400, 404, 405)
    print('Gateway rejected alternate paths, queries, encoded paths, destinations and methods')


def browser_route():
    try:
        urllib.request.urlopen(f'{RAICHO_URL}/connector/v1', timeout=5)
    except urllib.error.HTTPError as error:
        assert error.code == 404
    else:
        raise AssertionError('Connector route is exposed on the browser listener')
    print('Browser listener does not expose the connector')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('wait', 'routes', 'browser', 'deployment', 'snapshot', 'idle'))
    parser.add_argument('--status', default='connected')
    parser.add_argument('--previous-generation')
    parser.add_argument('--minimum-heartbeats', type=int, default=1)
    parser.add_argument('--timeout', type=int, default=120)
    arguments = parser.parse_args()
    if arguments.mode == 'wait':
        wait_for_status(arguments)
    else:
        {
            'routes': gateway_routes,
            'browser': browser_route,
            'deployment': deployment,
            'snapshot': snapshot,
            'idle': observe_idle,
        }[arguments.mode]()


if __name__ == '__main__':
    main()
