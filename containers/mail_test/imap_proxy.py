import re
import socket
import socketserver
import threading

from smtp_proxy import MESSAGE_LIMIT, read_line, write

LITERAL = re.compile(rb'\{([0-9]+)(\+)?\}\r\n$')
APPEND = re.compile(rb'^([^ ]+) APPEND (?:"Sent"|Sent)(?: |\r\n)', re.IGNORECASE)


def read_literal(stream, size: int) -> bytes:
    if size > MESSAGE_LIMIT:
        raise ValueError('Fixture IMAP literal exceeds size limit')
    content = stream.read(size)
    if len(content) != size:
        raise ValueError('Incomplete fixture IMAP literal')
    return content


def relay_commands(client, upstream, reply, state) -> None:
    while line := read_line(client):
        literal = LITERAL.search(line)
        append = APPEND.match(line)
        if append is not None and state.setting('imap') == 'reject_sent_append':
            if literal is not None and literal.group(2):
                read_literal(client, int(literal.group(1)))
                if read_line(client) != b'\r\n':
                    raise ValueError('Invalid fixture IMAP APPEND terminator')
            reply(append.group(1) + b' NO [OVERQUOTA] Fixture rejects Sent APPEND\r\n')
            state.record('sent_append_rejected')
            continue
        write(upstream, line)
        if literal is not None:
            write(upstream, read_literal(client, int(literal.group(1))))


class ImapHandler(socketserver.StreamRequestHandler):
    timeout = 120

    def handle(self):
        reply_lock = threading.Lock()

        def reply(content):
            with reply_lock:
                write(self.wfile, content)

        with socket.create_connection(
            (self.server.upstream, 3143), timeout=120
        ) as remote:

            def relay_responses():
                try:
                    while content := remote.recv(65536):
                        reply(content)
                except OSError:
                    pass
                finally:
                    self.request.shutdown(socket.SHUT_RD)

            response_thread = threading.Thread(target=relay_responses, daemon=True)
            response_thread.start()
            try:
                with remote.makefile('wb') as upstream:
                    relay_commands(self.rfile, upstream, reply, self.server.state)
            finally:
                remote.shutdown(socket.SHUT_RDWR)
                response_thread.join(timeout=5)
