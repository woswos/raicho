import socket
import unittest

from mailprobe.tests.probe.control_socket import (
    ControlBudgetSocket,
    ControlSocket,
    readable,
)


class ControlSocketTests(unittest.TestCase):
    def test_wire_budget_allows_full_control_message(self):
        reader, writer = socket.socketpair()
        self.addCleanup(reader.close)
        self.addCleanup(writer.close)
        wrapper = ControlBudgetSocket(reader)
        writer.sendall(b'x' * 65550)
        received = b''
        while len(received) < 65550:
            received += wrapper.recv(4096)
        self.assertEqual(len(received), 65550)

    def test_wire_budget_rejects_unbounded_fragmented_message(self):
        reader, writer = socket.socketpair()
        self.addCleanup(reader.close)
        self.addCleanup(writer.close)
        wrapper = ControlBudgetSocket(reader)
        wrapper.received = 131072
        writer.sendall(b'x')
        with self.assertRaises(ValueError):
            wrapper.recv(4096)

    def test_readable_uses_underlying_socket(self):
        reader, writer = socket.socketpair()
        self.addCleanup(reader.close)
        self.addCleanup(writer.close)
        connection = ControlSocket(None)
        connection.socket = reader
        self.assertFalse(readable(connection, 0))
        writer.sendall(b'x')
        self.assertTrue(readable(connection, 0))

    def test_readable_consumes_buffered_frame_without_network_data(self):
        connection = ControlSocket(None)
        connection._recv_queue = [{'opcode': 2, 'payload': b'{}'}]
        self.assertTrue(readable(connection, 0))


if __name__ == '__main__':
    unittest.main()
