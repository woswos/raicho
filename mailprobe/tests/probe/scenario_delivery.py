import time

from mailprobe.tests.probe.scenario_helpers import ATTACHMENT, ATTACHMENT_SHA256, IMMEDIATE_SUBJECT, QUEUED_SUBJECT


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
    immediate = client.command(
        'send',
        {
            'details': {
                'identityId': identity['id'],
                'to': ['recipient@raicho.test'],
                'subject': IMMEDIATE_SUBJECT,
                'body': '<p>Raicho <strong>HTML delivery</strong>.</p>',
                'deliveryFormat': 'html',
                'attachments': [ATTACHMENT],
            },
            'mode': 'sendNow',
        },
        timeout=30,
    )
    assert immediate['ok'], immediate
    assert immediate['result']['mode'] == 'sendNow', immediate
    delivered = received_once(client, IMMEDIATE_SUBJECT)
    message = delivered[0]
    assert identity['email'] in message['from'], message
    assert '<strong>HTML delivery</strong>' in message['html'], message
    assert any(
        attachment['filename'] == ATTACHMENT['name'] and attachment['sha256'] == ATTACHMENT_SHA256
        for attachment in message['attachments']
    ), message
    queued = client.call(
        'send',
        {
            'details': message_details(QUEUED_SUBJECT),
            'mode': 'sendLater',
        },
    )
    assert queued['mode'] == 'sendLater', queued
    queued_messages = client.call(
        'query',
        {
            'query': {'subject': QUEUED_SUBJECT},
        },
    )['messages']
    assert len(queued_messages) == 1, queued_messages
    assert not client.messages(QUEUED_SUBJECT)
    client.record(
        'delivery',
        {
            'immediate': immediate,
            'delivered': delivered,
            'queued': queued,
            'queued_message': queued_messages[0],
            'queued_subject': QUEUED_SUBJECT,
        },
    )
