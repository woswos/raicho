import argparse
import json
import socket
import sys
import urllib.error
import urllib.request

from automation.acceptance.connector.idle import observe_idle
from automation.acceptance.connector.status import (
    snapshot,
    wait_for_status,
)


def raw_request(request_line):
    with socket.create_connection(('gateway', 8081), timeout=5) as connection:
        connection.sendall(
            f'{request_line}\r\nHost: attacker.invalid\r\n'
            'Upgrade: websocket\r\nConnection: Upgrade\r\n'
            'Sec-WebSocket-Version: 13\r\n'
            'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n\r\n'.encode()
        )
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
    print(
        'Gateway rejected alternate paths, queries, encoded paths, destinations and methods'
    )


def browser_route():
    try:
        urllib.request.urlopen('http://raicho:8080/connector/v1', timeout=5)
    except urllib.error.HTTPError as error:
        assert error.code == 404
    else:
        raise AssertionError('Connector route is exposed on the browser listener')
    print('Browser listener does not expose the connector')


EXPECTED_NETWORKS = {
    'raicho': {'application', 'connector-application'},
    'gateway': {'connector-application', 'connector-thunderbird'},
    'thunderbird': {'thunderbird', 'connector-thunderbird'},
}


def networks(container):
    project = container['Config']['Labels']['com.docker.compose.project']
    return {
        name.removeprefix(f'{project}_')
        for name in container['NetworkSettings']['Networks']
    }


def deployment():
    containers = {
        container['Config']['Labels']['com.docker.compose.service']: container
        for container in json.load(sys.stdin)
    }
    gateway = containers['gateway']
    assert gateway['Config']['User'] == '10001:10001'
    assert gateway['HostConfig']['ReadonlyRootfs']
    assert gateway['HostConfig']['CapDrop'] == ['ALL']
    assert not gateway['HostConfig'].get('CapAdd')
    assert not gateway['HostConfig']['PortBindings']
    assert all(mount['Type'] == 'tmpfs' for mount in gateway['Mounts'])
    for service, expected in EXPECTED_NETWORKS.items():
        assert networks(containers[service]) == expected, service
    assert not networks(containers['raicho']) & networks(containers['thunderbird'])
    print(
        'Only the gateway bridges Raicho and Thunderbird, and it has no ports, '
        'secrets or data mounts'
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'mode', choices=('wait', 'routes', 'browser', 'deployment', 'snapshot', 'idle')
    )
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
