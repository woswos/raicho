import socket
import socketserver

LINE_LIMIT = 8192
MESSAGE_LIMIT = 1048576


def read_line(stream) -> bytes:
    line = stream.readline(LINE_LIMIT + 1)
    if len(line) > LINE_LIMIT or (line and not line.endswith(b'\r\n')):
        raise ValueError('Invalid or oversized fixture mail line')
    return line


def write(stream, content: bytes) -> None:
    stream.write(content)
    stream.flush()


def read_reply(stream) -> bytes:
    reply = read_line(stream)
    if len(reply) < 5 or not reply[:3].isdigit():
        raise ValueError('Invalid fixture SMTP response')
    result = [reply]
    while reply[3:4] == b'-':
        reply = read_line(stream)
        if len(reply) < 5 or reply[:3] != result[0][:3] or len(result) >= 32:
            raise ValueError('Invalid fixture SMTP multiline response')
        result.append(reply)
    return b''.join(result)


def filter_capabilities(reply: bytes) -> bytes:
    lines = [
        line[4:]
        for line in reply.splitlines(keepends=True)
        if line[4:].split()[0].upper() not in {b'STARTTLS', b'CHUNKING'}
    ]
    return b''.join(
        b'250' + (b' ' if index == len(lines) - 1 else b'-') + line
        for index, line in enumerate(lines)
    )


def relay_smtp(client, upstream, state) -> None:
    write(client, read_reply(upstream))
    while line := read_line(client):
        command = line.split(maxsplit=1)[0].upper()
        if command == b'RCPT' and state.setting('smtp') == 'reject':
            state.record('smtp_rejected')
            write(client, b'550 5.1.1 Fixture rejects recipient\r\n')
            continue
        if command in {b'STARTTLS', b'BDAT'}:
            write(client, b'502 Fixture supports plaintext DATA only\r\n')
            continue
        write(upstream, line)
        reply = read_reply(upstream)
        if command == b'EHLO' and reply.startswith(b'250'):
            reply = filter_capabilities(reply)
        write(client, reply)
        if command == b'QUIT':
            return
        if command != b'DATA' or not reply.startswith(b'354'):
            continue
        total_size = 0
        while True:
            content = read_line(client)
            total_size += len(content)
            if not content or total_size > MESSAGE_LIMIT:
                raise ValueError('Incomplete or oversized fixture SMTP message')
            write(upstream, content)
            if content == b'.\r\n':
                break
        reply = read_reply(upstream)
        if reply.startswith(b'250'):
            state.record('smtp_accepted')
            if state.setting('smtp') == 'drop_ack':
                state.record('smtp_ack_dropped')
                return
        write(client, reply)


class SmtpHandler(socketserver.StreamRequestHandler):
    timeout = 30

    def handle(self):
        with socket.create_connection(
            (self.server.upstream, 3025), timeout=30
        ) as remote:
            with remote.makefile('rwb') as upstream:
                relay_smtp(self, upstream, self.server.state)

    def readline(self, limit):
        return self.rfile.readline(limit)

    def write(self, content):
        return self.wfile.write(content)

    def flush(self):
        return self.wfile.flush()
