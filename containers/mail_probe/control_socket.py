import select

from probe_server import ProbeSocket
from websockify.websocket import WebSocket


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


class ControlSocket(ProbeSocket):
    def accept(self, connection, headers):
        WebSocket.accept(self, ControlBudgetSocket(connection), headers)


def readable(connection, timeout=0.1):
    return connection.pending() or bool(
        select.select([connection.socket], [], [], timeout)[0]
    )
