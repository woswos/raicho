GATEWAY_ADDRESS = ('gateway', 8081)
RAICHO_URL = 'http://raicho:8080'
STATUS_URL = f'{RAICHO_URL}/api/status'


def upgrade_request(request_line, host, key, origin=None):
    origin_header = f'Origin: {origin}\r\n' if origin else ''
    return (
        f'{request_line}\r\nHost: {host}\r\n{origin_header}'
        'Upgrade: websocket\r\nConnection: Upgrade\r\n'
        f'Sec-WebSocket-Version: 13\r\nSec-WebSocket-Key: {key}\r\n\r\n'
    ).encode()
