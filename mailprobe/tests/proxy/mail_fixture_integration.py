import imaplib
import smtplib
import unittest
from email.message import EmailMessage
from pathlib import Path

from fault_state import write_json
from mail_inspect import ensure_mailboxes, inspect_messages


class MailFixtureIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_mailboxes()

    def setUp(self):
        self.set_faults()

    def tearDown(self):
        self.set_faults()

    @staticmethod
    def set_faults(smtp='normal', imap='normal'):
        write_json(Path('/config/faults.json'), {'smtp': smtp, 'imap': imap})

    @staticmethod
    def message(suffix):
        message = EmailMessage()
        message['From'] = 'sender@raicho.test'
        message['To'] = 'recipient@raicho.test'
        message['Subject'] = f'Fixture {suffix}'
        message['Message-ID'] = f'<fixture-{suffix}@raicho.test>'
        message.set_content('Fictional fixture content')
        return message

    def send(self, message):
        with smtplib.SMTP('127.0.0.1', 3025, timeout=10) as client:
            client.login('sender', 'fixture')
            client.send_message(message)

    def count(self, message, **location):
        return sum(
            item['message_id'] == message['Message-ID']
            for item in inspect_messages(**location)
        )

    def test_normal_submission_arrives_once(self):
        message = self.message('normal')
        self.send(message)
        self.assertEqual(self.count(message), 1)

    def test_rejected_submission_never_arrives(self):
        message = self.message('rejected')
        self.set_faults(smtp='reject')
        with self.assertRaises(smtplib.SMTPRecipientsRefused):
            self.send(message)
        self.assertEqual(self.count(message), 0)

    def test_lost_acknowledgment_still_delivers_once(self):
        message = self.message('lost-ack')
        self.set_faults(smtp='drop_ack')
        with self.assertRaises(smtplib.SMTPServerDisconnected):
            self.send(message)
        self.assertEqual(self.count(message), 1)

    def test_sent_append_rejection_keeps_drafts_available(self):
        message = self.message('append')
        self.set_faults(imap='reject_sent_append')
        with imaplib.IMAP4('127.0.0.1', 3143, timeout=10) as client:
            client.login('sender', 'fixture')
            status, _result = client.append('Sent', None, None, message.as_bytes())
            self.assertEqual(status, 'NO')
            status, _result = client.append('Drafts', None, None, message.as_bytes())
            self.assertEqual(status, 'OK')
        self.assertEqual(self.count(message, username='sender', folder='Sent'), 0)
        self.assertEqual(self.count(message, username='sender', folder='Drafts'), 1)


if __name__ == '__main__':
    unittest.main()
