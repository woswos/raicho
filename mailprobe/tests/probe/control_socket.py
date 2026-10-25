import select

from websockify.websocketserver import HttpWebSocket


class ControlBudgetSocket:
    def __init__(self, connection):
        self.connection = connection
        self.received = 0

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def recv(self, size):
        content = self.connection.recv(size)
        self.received += len(content)
        if self.received > 131072:
            raise ValueError('Mail fixture wire message exceeded its size limit')
        return content


class ControlSocket(HttpWebSocket):
    def accept(self, connection, headers):
        super().accept(ControlBudgetSocket(connection), headers)

    def _decode_hybi(self, content):
        frame = super()._decode_hybi(content)
        # Websockify normally rejects text frames because VNC uses binary data.
        if frame is not None and frame['opcode'] == 1:
            frame['opcode'] = 2
        return frame


def readable(connection, timeout=0.1):
    return connection.pending() or bool(
        select.select([connection.socket], [], [], timeout)[0]
    )
