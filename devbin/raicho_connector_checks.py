import argparse
import json
import socket
import sys
import urllib.error
import urllib.request

from raicho_connector_idle import observe_idle
from raicho_connector_status import snapshot, wait_for_status


def raw_request(request_line):
    with socket.create_connection(('connector-proxy', 8081), timeout=5) as connection:
        connection.sendall(
            f'{request_line}\r\nHost: attacker.invalid\r\n'
            'Upgrade: websocket\r\nConnection: Upgrade\r\n'
            'Sec-WebSocket-Version: 13\r\n'
            'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n\r\n'.encode()
        )
        response = connection.recv(1024).split(b'\r\n', 1)[0]
    return int(response.split()[1])


def proxy_routes():
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
        'Proxy rejected alternate paths, queries, encoded paths, destinations and methods'
    )


def browser_route():
    try:
        urllib.request.urlopen('http://raicho:8080/connector/v1', timeout=5)
    except urllib.error.HTTPError as error:
        assert error.code == 404
    else:
        raise AssertionError('Connector route is exposed on the browser listener')
    print('Browser listener does not expose the connector')


def deployment():
    containers = json.load(sys.stdin)
    proxy = next(
        container
        for container in containers
        if container['Config']['Labels']['com.docker.compose.service']
        == 'connector_proxy'
    )
    assert proxy['Config']['User'] == '10001:10001'
    assert proxy['HostConfig']['ReadonlyRootfs']
    assert proxy['HostConfig']['CapDrop'] == ['ALL']
    assert not proxy['HostConfig'].get('CapAdd')
    assert not proxy['HostConfig']['PortBindings']
    assert all(mount['Type'] == 'tmpfs' for mount in proxy['Mounts'])
    assert len(proxy['NetworkSettings']['Networks']) == 2
    for container in containers:
        if container is not proxy:
            assert len(container['NetworkSettings']['Networks']) == 1
    print(
        'Proxy is the only dual-network service and has no ports, secrets or data mounts'
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
            'routes': proxy_routes,
            'browser': browser_route,
            'deployment': deployment,
            'snapshot': snapshot,
            'idle': observe_idle,
        }[arguments.mode]()


if __name__ == '__main__':
    main()
