import io
import unittest

from smtp_proxy import relay_smtp


class MockConnection:
    def __init__(self, received):
        self.input = io.BytesIO(received)
        self.output = io.BytesIO()

    def readline(self, limit):
        return self.input.readline(limit)

    def write(self, content):
        return self.output.write(content)

    def flush(self):
        pass


class MockState:
    def __init__(self, mode):
        self.mode = mode
        self.events = []

    def setting(self, _name):
        return self.mode

    def record(self, event):
        self.events.append(event)


class SmtpProxyTests(unittest.TestCase):
    def test_rejects_recipient_before_upstream_delivery(self):
        client = MockConnection(b'RCPT TO:<recipient@raicho.test>\r\nQUIT\r\n')
        upstream = MockConnection(b'220 ready\r\n221 bye\r\n')
        state = MockState('reject')
        relay_smtp(client, upstream, state)
        self.assertIn(b'550', client.output.getvalue())
        self.assertEqual(upstream.output.getvalue(), b'QUIT\r\n')
        self.assertEqual(state.events, ['smtp_rejected'])

    def test_delivers_data_but_drops_acceptance_acknowledgment(self):
        client = MockConnection(b'DATA\r\nSubject: fixture\r\n\r\nBody\r\n.\r\n')
        upstream = MockConnection(b'220 ready\r\n354 continue\r\n250 stored\r\n')
        state = MockState('drop_ack')
        relay_smtp(client, upstream, state)
        self.assertIn(b'Body\r\n.\r\n', upstream.output.getvalue())
        self.assertNotIn(b'250 stored', client.output.getvalue())
        self.assertEqual(state.events, ['smtp_accepted', 'smtp_ack_dropped'])

    def test_relays_successful_submission_once(self):
        client = MockConnection(b'DATA\r\nBody\r\n.\r\nQUIT\r\n')
        upstream = MockConnection(
            b'220 ready\r\n354 continue\r\n250 stored\r\n221 bye\r\n'
        )
        state = MockState('normal')
        relay_smtp(client, upstream, state)
        self.assertIn(b'250 stored', client.output.getvalue())
        self.assertEqual(state.events, ['smtp_accepted'])

    def test_removes_encrypted_and_chunked_transport_capabilities(self):
        client = MockConnection(b'EHLO raicho.test\r\nQUIT\r\n')
        upstream = MockConnection(
            b'220 ready\r\n250-server\r\n250-STARTTLS\r\n250-CHUNKING\r\n250 AUTH PLAIN\r\n221 bye\r\n'
        )
        relay_smtp(client, upstream, MockState('normal'))
        self.assertNotIn(b'STARTTLS', client.output.getvalue())
        self.assertNotIn(b'CHUNKING', client.output.getvalue())
        self.assertIn(b'250 AUTH PLAIN\r\n', client.output.getvalue())

    def test_incomplete_data_is_not_recorded_as_accepted(self):
        state = MockState('normal')
        with self.assertRaises(ValueError):
            relay_smtp(
                MockConnection(b'DATA\r\nbody\r\n'),
                MockConnection(b'220 ready\r\n354 continue\r\n'),
                state,
            )
        self.assertEqual(state.events, [])

    def test_rejected_data_is_not_recorded_as_accepted(self):
        state = MockState('normal')
        relay_smtp(
            MockConnection(b'DATA\r\nbody\r\n.\r\n'),
            MockConnection(b'220 ready\r\n354 continue\r\n550 rejected\r\n'),
            state,
        )
        self.assertEqual(state.events, [])


if __name__ == '__main__':
    unittest.main()
