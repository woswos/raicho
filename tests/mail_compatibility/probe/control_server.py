import argparse
import hmac
import json
import socketserver
from pathlib import Path

from control_socket import ControlSocket, readable
from control_state import ControlState
from websockify.websocket import WebSocketWantReadError
from websockify.websocketserver import WebSocketRequestHandler, WebSocketServer


class ControlHandler(WebSocketRequestHandler):
    protocol_version = 'HTTP/1.1'
    SocketClass = ControlSocket

    def setup(self):
        self.request.settimeout(10)
        super().setup()

    def log_message(self, *_arguments):
        pass

    def authenticated(self):
        supplied = self.headers.get('Authorization', '')
        return hmac.compare_digest(supplied, f'Bearer {self.server.state.token}')

    def reply(self, status, payload):
        content = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if not self.authenticated() or self.path != '/status':
            self.reply(404, {})
            return
        self.reply(200, self.server.state.status())

    def do_POST(self):
        if not self.authenticated() or self.path != '/command':
            self.reply(404, {})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 65536:
                raise ValueError('Invalid command size.')
            request = json.loads(self.rfile.read(length))
            response = self.server.state.submit(
                request['action'],
                request.get('arguments', {}),
                timeout=min(180, max(1, request.get('timeout', 120))),
                drop_result=request.get('drop_result', False),
            )
            self.reply(200, response)
        except (ValueError, KeyError, TypeError):
            self.reply(400, {'ok': False, 'error': 'Invalid or unavailable command.'})

    def handle_upgrade(self):
        if self.path != '/connector/v1':
            self.send_error(404)
            return
        super().handle_upgrade()

    def handle_websocket(self):
        session = None
        try:
            self.request.socket.settimeout(5)
            greeting = self.receive()
            if (
                not isinstance(greeting, dict)
                or greeting.get('type') != 'mail_probe'
                or not hmac.compare_digest(
                    greeting.get('token', ''), self.server.state.token
                )
            ):
                return
            session = self.server.state.connect(
                greeting['session_id'],
                greeting['browser_version'],
                greeting['extension_version'],
            )
            self.request.socket.settimeout(185)
            while True:
                command = self.server.state.next_command(session)
                if command is not None:
                    self.request.sendmsg(json.dumps(command).encode())
                if not readable(self.request):
                    continue
                message = self.receive()
                if message is None:
                    return
                if not self.server.state.finish(session, message):
                    return
        except (OSError, ValueError, KeyError, TypeError):
            return
        finally:
            if session is not None:
                self.server.state.disconnect(session)

    def receive(self):
        while True:
            try:
                payload = self.request.recvmsg()
                if payload is None:
                    return None
                self.request.socket.received = 0
                if len(payload) > 65536:
                    raise ValueError('Probe result too large.')
                message = json.loads(payload.decode('utf-8'))
                if not isinstance(message, dict):
                    raise ValueError('Probe result must be an object.')
                return message
            except WebSocketWantReadError:
                continue


class ControlServer(socketserver.ThreadingMixIn, WebSocketServer):
    daemon_threads = True

    def __init__(self, directory):
        self.state = ControlState(directory)
        super().__init__(('0.0.0.0', 8765), ControlHandler)

    def handle_error(self, _request, _client_address):
        print('Mail probe connection failed.', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, default=Path('/config'))
    arguments = parser.parse_args()
    with ControlServer(arguments.directory) as server:
        (arguments.directory / 'control_ready').write_text('ready\n')
        server.serve_forever()


if __name__ == '__main__':
    main()
