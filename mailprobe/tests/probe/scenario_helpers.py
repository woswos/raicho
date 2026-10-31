import hashlib

from mailprobe.tests.probe.client import wait_until

ATTACHMENT = {'name': 'probe.txt', 'content': 'Raicho fixture attachment\n', 'type': 'text/plain'}
ATTACHMENT_SHA256 = hashlib.sha256(ATTACHMENT['content'].encode()).hexdigest()

IMMEDIATE_SUBJECT = 'Raicho probe immediate send'
QUEUED_SUBJECT = 'Raicho probe queued send'
MISSING_RECIPIENT_SUBJECT = 'Raicho probe missing recipient'
MISSING_IDENTITY_SUBJECT = 'Raicho probe missing identity'
REJECTED_SUBJECT = 'Raicho probe SMTP rejection'
LOST_RESULT_SUBJECT = 'Raicho probe lost controller result'
LOST_ACKNOWLEDGMENT_SUBJECT = 'Raicho probe lost SMTP acknowledgment'
SENT_COPY_FAILURE_SUBJECT = 'Raicho probe Sent copy failure'
DELIVERED_SUBJECTS = (IMMEDIATE_SUBJECT, LOST_RESULT_SUBJECT, LOST_ACKNOWLEDGMENT_SUBJECT, SENT_COPY_FAILURE_SUBJECT)
UNDELIVERED_SUBJECTS = (QUEUED_SUBJECT, REJECTED_SUBJECT, MISSING_IDENTITY_SUBJECT, MISSING_RECIPIENT_SUBJECT)


def query(client, subject):
    response = client.command('query', {'query': {'subject': subject}}, timeout=10)
    assert response['ok'], response
    return response['result']['messages']


def message_parts(part):
    yield part
    for child in part.get('parts', []):
        yield from message_parts(child)


def wait_query(client, subject, count, body=None):
    def matching():
        messages = query(client, subject)
        if len(messages) != count:
            return None
        if body is None:
            return messages
        response = client.command('get_message', {'message_id': messages[0]['id']}, timeout=10)
        assert response['ok'], response
        if any(body in part.get('body', '') for part in message_parts(response['result']['full'])):
            return messages
        return None

    return wait_until(matching, 30, f'Expected fixture messages did not become queryable: {subject}')


def saved_message(client, details):
    before = {message['id'] for message in query(client, details['subject'])}
    result = client.call('save', {'details': details})
    assert result['mode'] == 'draft', result
    client.record('save_response_' + details['subject'], result)
    if result['messages']:
        assert len(result['messages']) == 1, result
        return result['messages'][0]

    def saved():
        matches = [message for message in query(client, details['subject']) if message['id'] not in before]
        return matches[0] if len(matches) == 1 else None

    return wait_until(saved, 30, 'Saved fixture draft did not become queryable.')


def save_native_target(client, details):
    return saved_message(
        client,
        {
            **details,
            'subject': 'Raicho probe native draft',
            'attachments': [ATTACHMENT],
        },
    )
