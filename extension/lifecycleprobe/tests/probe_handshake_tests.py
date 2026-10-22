import http.client
import json
import struct
import tempfile
import threading
import time
import unittest
from pathlib import Path

from probe_server import ProbeServer


class ProbeHandshakeTests(unittest.TestCase):
    def test_http_upgrade_constructs_the_socket_and_sends_the_handshake(self):
        with (
            tempfile.TemporaryDirectory() as temporary,
            ProbeServer(Path(temporary), ('127.0.0.1', 0)) as server,
        ):
            worker = threading.Thread(
                target=server.serve_forever,
                kwargs={'poll_interval': 0.01},
                daemon=True,
            )
            worker.start()
            connection = http.client.HTTPConnection(*server.server_address, timeout=2)
            try:
                connection.request(
                    'GET',
                    '/connector/v1',
                    headers={
                        'Upgrade': 'websocket',
                        'Connection': 'Upgrade',
                        'Sec-WebSocket-Version': '13',
                        'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
                    },
                )
                response = connection.getresponse()
                try:
                    self.assertEqual(response.version, 11)
                    self.assertEqual(response.status, 101)
                    self.assertEqual(
                        response.getheader('Sec-WebSocket-Accept'),
                        's3pPLMBiTxaQ9kYGzzhZRbK+xOo=',
                    )
                    greeting = json.dumps(
                        {
                            'type': 'lifecycle_probe',
                            'sequence': 0,
                            'token': server.probe_state.token,
                            'session_id': '00000000-0000-0000-0000-000000000001',
                            'extension_version': '0.1.0',
                            'browser_version': '153.5.0',
                        }
                    ).encode()
                    mask = bytes(range(4))
                    payload = bytes(
                        value ^ mask[index % 4] for index, value in enumerate(greeting)
                    )
                    connection.sock.sendall(
                        struct.pack('!BBH', 0x81, 0xFE, len(payload)) + mask + payload
                    )
                    deadline = time.monotonic() + 2
                    while (
                        not server.probe_state.snapshot()['sessions']
                        and time.monotonic() < deadline
                    ):
                        time.sleep(0.01)
                    self.assertEqual(len(server.probe_state.snapshot()['sessions']), 1)
                finally:
                    response.close()
            finally:
                connection.close()
                server.shutdown()
                worker.join(timeout=2)
                self.assertFalse(worker.is_alive())


if __name__ == '__main__':
    unittest.main()
