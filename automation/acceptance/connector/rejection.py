import base64
import hashlib
import json
import secrets
import socket
import struct

from automation.acceptance.connector.endpoints import GATEWAY_ADDRESS, upgrade_request
from automation.acceptance.connector.privacy import MAIL_CANARIES
from automation.paths import REPOSITORY_ROOT

LIMITS = json.loads((REPOSITORY_ROOT / 'protocol/limits.json').read_text())


def receive(connection, length):
    output = bytearray()
    while len(output) < length:
        chunk = connection.recv(length - len(output))
        assert chunk, 'WebSocket closed before the rejection completed'
        output.extend(chunk)
    return bytes(output)


def frame(connection):
    header = receive(connection, 2)
    assert header[0] & 0xF0 == 0x80, 'Expected one complete uncompressed frame'
    assert not header[1] & 0x80, 'Server frame must be unmasked'
    length = header[1]
    if length == 126:
        length = struct.unpack('!H', receive(connection, 2))[0]
    assert length < 126, 'Rejection frame exceeded the fixture bound'
    return header[0] & 0x0F, receive(connection, length)


def send(connection, opcode, contents):
    mask = secrets.token_bytes(4)
    length = len(contents)
    header = bytes((0x80 | opcode, 0x80 | min(length, 126)))
    if length >= 126:
        header += struct.pack('!H', length)
    masked = bytes(value ^ mask[index % 4] for index, value in enumerate(contents))
    connection.sendall(header + mask + masked)


def reject(mail=False):
    with socket.create_connection(GATEWAY_ADDRESS, timeout=8) as connection:
        key = base64.b64encode(secrets.token_bytes(16)).decode()
        connection.sendall(
            upgrade_request(
                'GET /connector/v1 HTTP/1.1',
                'gateway:8081',
                key,
                origin='moz-extension://12345678-1234-1234-1234-123456789abc',
            )
        )
        response = bytearray()
        while not response.endswith(b'\r\n\r\n'):
            assert len(response) < 4096, 'Upgrade headers exceeded the fixture bound'
            response.extend(receive(connection, 1))
        assert response.startswith(b'HTTP/1.1 101 '), 'WebSocket upgrade failed'
        accept = base64.b64encode(hashlib.sha1((key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest())
        headers = {
            name.lower(): value.strip()
            for name, value in (line.split(b':', 1) for line in bytes(response).split(b'\r\n')[1:-2])
        }
        assert headers[b'sec-websocket-accept'] == accept
        opcode, contents = frame(connection)
        assert opcode == 1
        assert json.loads(contents)['type'] == 'challenge'
        payload = {
            'type': 'authenticate',
            'protocol_version': 1,
            'client_nonce': secrets.token_hex(32),
            'client_proof': secrets.token_hex(32),
            'backend_kind': 'thunderbird',
            'backend_version': 'fixture',
            'connector_version': 'fixture',
            'capabilities': [],
        }
        if mail:
            payload |= dict(
                zip(
                    ('subject', 'body', 'sender'),
                    (value.decode() for value in MAIL_CANARIES),
                    strict=True,
                )
            )
        send(
            connection,
            1,
            json.dumps(payload).encode(),
        )
        opcode, contents = frame(connection)
        assert opcode == 1
        message = json.loads(contents)
        assert message['type'] == 'error'
        assert message['code'] == ('invalid_message' if mail else 'authentication_failed')
        opcode, contents = frame(connection)
        assert opcode == 8
        assert struct.unpack('!H', contents[:2])[0] == (
            LIMITS['protocol_failure_close_code'] if mail else LIMITS['authentication_failure_close_code']
        )
        send(connection, 8, contents)
    print('Gateway forwarded the bounded rejection without reflecting input')


if __name__ == '__main__':
    reject()
    reject(mail=True)
