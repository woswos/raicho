import unittest
from unittest.mock import Mock

from probe_server import BudgetSocket, ProbeHandler, ProbeSocket


class ProbeSocketTests(unittest.TestCase):
    def test_wire_budget_bounds_partial_messages(self):
        connection = Mock()
        connection.recv.return_value = b'x' * 4096
        wrapped = BudgetSocket(connection)
        self.assertEqual(len(wrapped.recv(4096)), 4096)
        self.assertEqual(len(wrapped.recv(4096)), 4096)
        with self.assertRaises(ValueError):
            wrapped.recv(4096)

    def test_completed_message_can_reset_budget(self):
        connection = Mock()
        connection.recv.return_value = b'x' * 4096
        wrapped = BudgetSocket(connection)
        wrapped.recv(4096)
        wrapped.recv(4096)
        wrapped.received = 0
        self.assertEqual(len(wrapped.recv(4096)), 4096)

    def test_socket_operations_are_forwarded(self):
        connection = Mock()
        wrapped = BudgetSocket(connection)
        wrapped.settimeout(35)
        connection.settimeout.assert_called_once_with(35)

    def test_text_frames_reuse_library_decoder_with_binary_payload_assembly(self):
        decoded = ProbeSocket()._decode_hybi(b'\x81\x0e{"sequence":0}')
        self.assertEqual(decoded['opcode'], 2)
        self.assertEqual(decoded['payload'], b'{"sequence":0}')

    def test_incomplete_frames_remain_incomplete(self):
        self.assertIsNone(ProbeSocket()._decode_hybi(b'\x81'))

    def test_ping_frames_keep_their_control_opcode(self):
        decoded = ProbeSocket()._decode_hybi(b'\x89\x00')
        self.assertEqual(decoded['opcode'], 9)

    def test_closed_websocket_does_not_access_cleared_socket(self):
        handler = object.__new__(ProbeHandler)
        handler.request = Mock(socket=None)
        handler.request.recvmsg.return_value = None
        handler.handle_websocket()


if __name__ == '__main__':
    unittest.main()
