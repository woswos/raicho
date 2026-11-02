import hashlib
import imaplib
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser

HOST = 'greenmail'
PORT = 3143
PASSWORD = 'fixture'


def describe_message(uid: bytes, content: bytes) -> dict:
    message = BytesParser(policy=policy.default).parsebytes(content)
    description = {
        'uid': uid.decode('ascii'),
        'message_id': str(message.get('Message-ID', '')),
        'from': str(message.get('From', '')),
        'to': str(message.get('To', '')),
        'subject': str(message.get('Subject', '')),
        'plain': '',
        'html': '',
        'attachments': [],
    }
    for part in message.walk():
        if part.is_multipart():
            continue
        payload = part.get_payload(decode=True) or b''
        if part.get_content_disposition() == 'attachment' or part.get_filename():
            description['attachments'].append(
                {
                    'filename': part.get_filename(),
                    'type': part.get_content_type(),
                    'size': len(payload),
                    'sha256': hashlib.sha256(payload).hexdigest(),
                }
            )
        elif part.get_content_type() in {'text/plain', 'text/html'}:
            kind = part.get_content_subtype()
            description[kind] += payload.decode(part.get_content_charset() or 'utf-8')
    return description


def inspect_messages(username='recipient', folder='INBOX') -> list[dict]:
    with imaplib.IMAP4(HOST, PORT, timeout=10) as client:
        client.login(username, PASSWORD)
        status, _result = client.select(folder, readonly=True)
        if status != 'OK':
            raise ValueError(f'Fixture mailbox is unavailable: {folder}')
        status, result = client.uid('SEARCH', None, 'UNDELETED')
        if status != 'OK':
            raise ValueError('Fixture mailbox search failed')
        messages = []
        for uid in result[0].split():
            status, parts = client.uid('FETCH', uid, '(BODY.PEEK[])')
            if status != 'OK':
                raise ValueError('Fixture message fetch failed')
            content = next((part[1] for part in parts if isinstance(part, tuple)), None)
            if not isinstance(content, bytes):
                raise ValueError('Fixture message fetch returned no content')
            messages.append(describe_message(uid, content))
        return messages


def append_message(username: str, folder: str, message: EmailMessage) -> None:
    with imaplib.IMAP4(HOST, PORT, timeout=10) as client:
        client.login(username, PASSWORD)
        status, _result = client.append(folder, None, None, message.as_bytes())
        if status != 'OK':
            raise ValueError(f'Could not append a fixture message to {folder}')


def ensure_mailboxes() -> None:
    with imaplib.IMAP4(HOST, PORT, timeout=10) as client:
        client.login('sender', PASSWORD)
        for folder in ['Drafts', 'Sent', 'Trash']:
            status, _result = client.create(folder)
            if status != 'OK':
                status, _result = client.select(folder, readonly=True)
                if status != 'OK':
                    raise ValueError(f'Could not prepare fixture mailbox: {folder}')
            client.subscribe(folder)
