import io
import unittest

from imap_proxy import relay_commands
from smtp_proxy_tests import MockState


class ImapProxyTests(unittest.TestCase):
    def relay(self, content, mode='normal'):
        upstream = io.BytesIO()
        replies = []
        state = MockState(mode)
        relay_commands(io.BytesIO(content), upstream, replies.append, state)
        return upstream.getvalue(), b''.join(replies), state.events

    def test_rejects_synchronizing_sent_append_before_literal(self):
        upstream, replies, events = self.relay(
            b'one APPEND "Sent" (\\Seen) {20}\r\ntwo NOOP\r\n',
            'reject_sent_append',
        )
        self.assertEqual(upstream, b'two NOOP\r\n')
        self.assertEqual(replies, b'one NO [OVERQUOTA] Fixture rejects Sent APPEND\r\n')
        self.assertEqual(events, ['sent_append_rejected'])

    def test_discards_nonsynchronizing_rejected_literal(self):
        upstream, replies, _events = self.relay(
            b'one APPEND Sent {4+}\r\nbody\r\ntwo NOOP\r\n', 'reject_sent_append'
        )
        self.assertEqual(upstream, b'two NOOP\r\n')
        self.assertIn(b'one NO', replies)

    def test_keeps_draft_append_and_literal_intact(self):
        content = b'one APPEND "Drafts" {19}\r\na APPEND Sent {5}\r\n\r\ntwo NOOP\r\n'
        upstream, replies, events = self.relay(content, 'reject_sent_append')
        self.assertEqual(upstream, content)
        self.assertEqual(replies, b'')
        self.assertEqual(events, [])

    def test_forwards_normal_sent_append(self):
        content = b'one APPEND Sent {4}\r\nbody\r\ntwo NOOP\r\n'
        self.assertEqual(self.relay(content)[0], content)

    def test_incomplete_literal_fails(self):
        with self.assertRaises(ValueError):
            self.relay(b'one APPEND Drafts {20}\r\nshort')

    def test_oversized_literal_fails(self):
        with self.assertRaises(ValueError):
            self.relay(b'one APPEND Drafts {1048577}\r\n')


if __name__ == '__main__':
    unittest.main()
