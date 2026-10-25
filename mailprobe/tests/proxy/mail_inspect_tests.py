import unittest
from email.message import EmailMessage

from mailprobe.tests.proxy.mail_inspect import describe_message


class MailInspectTests(unittest.TestCase):
    def test_describes_plain_html_and_attachment_without_decoding_binary_as_body(self):
        message = EmailMessage()
        message['Message-ID'] = '<fixture@raicho.test>'
        message['From'] = 'Selected Identity <sender@raicho.test>'
        message['Subject'] = 'Fixture'
        message.set_content('Plain fixture')
        message.add_alternative('<p>HTML fixture</p>', subtype='html')
        message.add_attachment(
            b'attachment', maintype='text', subtype='plain', filename='fixture.txt'
        )
        description = describe_message(b'42', message.as_bytes())
        self.assertEqual(description['uid'], '42')
        self.assertEqual(description['message_id'], '<fixture@raicho.test>')
        self.assertIn('Plain fixture', description['plain'])
        self.assertIn('<p>HTML fixture</p>', description['html'])
        self.assertEqual(description['attachments'][0]['filename'], 'fixture.txt')
        self.assertEqual(description['attachments'][0]['size'], 10)
        self.assertNotIn('attachment', description['plain'])

    def test_missing_message_id_remains_empty(self):
        self.assertEqual(
            describe_message(b'1', b'Subject: fixture\r\n\r\nbody')['message_id'], ''
        )


if __name__ == '__main__':
    unittest.main()
