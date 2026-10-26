import argparse
import contextlib
import socketserver
import threading
from pathlib import Path

from mailprobe.tests.proxy.fault_state import FaultState
from mailprobe.tests.proxy.imap import ImapHandler
from mailprobe.tests.proxy.smtp import SmtpHandler


class FaultServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, address, handler, upstream, state):
        self.upstream = upstream
        self.state = state
        super().__init__(address, handler)

    def handle_error(self, _request, _client_address):
        self.state.record('proxy_error')
        print('Fixture mail proxy connection ended unexpectedly', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, default=Path('/fixture'))
    parser.add_argument('--upstream', default='greenmail')
    arguments = parser.parse_args()
    state = FaultState(arguments.directory)
    with contextlib.ExitStack() as stack:
        servers = [
            stack.enter_context(
                FaultServer(('0.0.0.0', port), handler, arguments.upstream, state)
            )
            for port, handler in [(3025, SmtpHandler), (3143, ImapHandler)]
        ]
        for server in servers:
            threading.Thread(target=server.serve_forever, daemon=True).start()
        (arguments.directory / 'mail_proxy_ready').write_text('ready\n')
        threading.Event().wait()


if __name__ == '__main__':
    main()
