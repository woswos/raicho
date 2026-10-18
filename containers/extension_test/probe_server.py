import argparse
import socketserver
import sys
import traceback
from pathlib import Path

from probe_state import ProbeState
from websockify.websocket import WebSocket, WebSocketWantReadError
from websockify.websocketserver import WebSocketRequestHandler, WebSocketServer


class BudgetSocket:
    def __init__(self, connection):
        self.connection = connection
        self.received = 0

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def recv(self, size):
        content = self.connection.recv(size)
        self.received += len(content)
        if self.received > 8192:
            raise ValueError('Fixture wire message exceeded its size limit')
        return content


class ProbeSocket(WebSocket):
    def accept(self, connection, headers):
        super().accept(BudgetSocket(connection), headers)

    def _decode_hybi(self, content):
        frame = super()._decode_hybi(content)
        # Websockify normally rejects text frames because VNC uses binary data.
        if frame is not None and frame['opcode'] == 1:
            frame['opcode'] = 2
        return frame


class ProbeHandler(WebSocketRequestHandler):
    SocketClass = ProbeSocket

    def log_message(self, *_arguments):
        pass

    def setup(self):
        self.request.settimeout(5)
        super().setup()

    def handle_upgrade(self):
        if self.path != '/connector/v1':
            self.send_error(404)
            return
        super().handle_upgrade()

    def do_GET(self):
        self.send_error(404)

    def handle_websocket(self):
        session_id = None
        phase = 'receive'
        try:
            while True:
                phase = 'receive'
                try:
                    payload = self.request.recvmsg()
                except WebSocketWantReadError:
                    continue
                if payload is None:
                    return
                self.request.socket.received = 0
                if session_id is None:
                    phase = 'authentication'
                    session_id = self.server.probe_state.connect(
                        payload, self.headers.get('Origin')
                    )
                    self.request.socket.settimeout(35)
                else:
                    phase = 'heartbeat'
                    self.server.probe_state.heartbeat(session_id, payload)
        except (TimeoutError, ValueError) as error:
            print(f'Fixture rejected {phase}: {type(error).__name__}', flush=True)
            self.server.probe_state.reject()
        except OSError:
            if session_id is None:
                self.server.probe_state.reject()


class ProbeServer(socketserver.ThreadingMixIn, WebSocketServer):
    daemon_threads = True

    def __init__(self, directory, address=('0.0.0.0', 8765)):
        self.probe_state = ProbeState(directory)
        super().__init__(address, ProbeHandler)

    def handle_error(self, _request, _client_address):
        error = sys.exception()
        location = traceback.extract_tb(error.__traceback__)[-1]
        print(
            f'Fixture handler failed: {type(error).__name__} '
            f'at {Path(location.filename).name}:{location.lineno}',
            flush=True,
        )
        self.probe_state.reject()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, default=Path('/fixture'))
    arguments = parser.parse_args()
    arguments.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    ready_path = arguments.directory / 'ready'
    ready_path.unlink(missing_ok=True)
    with ProbeServer(arguments.directory) as server:
        ready_path.write_text('ready\n')
        try:
            server.serve_forever()
        finally:
            ready_path.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
