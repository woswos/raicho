import hashlib
import time


def message_details(subject):
    return {
        'to': ['recipient@raicho.test'],
        'subject': subject,
        'plainTextBody': 'Fictional Raicho delivery fixture.',
        'isPlainText': True,
    }


def send_message(client, subject, **options):
    return client.command(
        'send',
        {
            'details': message_details(subject),
            'mode': 'sendNow',
        },
        timeout=30,
        **options,
    )


def received_once(client, subject):
    client.wait_messages(subject, 1)
    time.sleep(2)
    messages = client.messages(subject)
    assert len(messages) == 1, messages
    return messages


def run(client):
    client.faults()
    identity = client.read_record('drafts')['identity']
    immediate_subject = 'Raicho probe immediate send'
    attachment_content = 'Raicho fixture attachment\n'
    immediate = client.command(
        'send',
        {
            'details': {
                'identityId': identity['id'],
                'to': ['recipient@raicho.test'],
                'subject': immediate_subject,
                'body': '<p>Raicho <strong>HTML delivery</strong>.</p>',
                'deliveryFormat': 'html',
                'attachments': [
                    {
                        'name': 'probe.txt',
                        'content': attachment_content,
                        'type': 'text/plain',
                    }
                ],
            },
            'mode': 'sendNow',
        },
        timeout=30,
    )
    assert immediate['ok'], immediate
    assert immediate['result']['mode'] == 'sendNow', immediate
    delivered = received_once(client, immediate_subject)
    message = delivered[0]
    assert identity['email'] in message['from'], message
    assert '<strong>HTML delivery</strong>' in message['html'], message
    assert any(
        attachment['filename'] == 'probe.txt'
        and attachment['sha256']
        == hashlib.sha256(attachment_content.encode()).hexdigest()
        for attachment in message['attachments']
    ), message
    queued_subject = 'Raicho probe queued send'
    queued = client.call(
        'send',
        {
            'details': message_details(queued_subject),
            'mode': 'sendLater',
        },
    )
    assert queued['mode'] == 'sendLater', queued
    queued_messages = client.call(
        'query',
        {
            'query': {'subject': queued_subject},
        },
    )['messages']
    assert len(queued_messages) == 1, queued_messages
    assert not client.messages(queued_subject)
    client.record(
        'delivery',
        {
            'immediate': immediate,
            'delivered': delivered,
            'queued': queued,
            'queued_message': queued_messages[0],
            'queued_subject': queued_subject,
        },
    )
