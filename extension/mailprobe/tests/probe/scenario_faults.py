from scenario_delivery import message_details, received_once, send_message


def verify_fault_events(before, after, *, accepted, required=()):
    counters = set(before) | set(after) | {'smtp_accepted'} | set(required)
    delta = {name: after.get(name, 0) - before.get(name, 0) for name in counters}
    assert all(value >= 0 for value in delta.values()), delta
    assert delta['smtp_accepted'] == accepted, delta
    assert all(delta[name] >= 1 for name in required), delta
    return delta


def run(client):
    invalid_extension = client.command(
        'send',
        {
            'details': {'subject': 123},
            'mode': 'sendNow',
        },
        timeout=15,
    )
    assert not invalid_extension['ok'], invalid_extension
    invalid_api = client.command(
        'send',
        {
            'details': {'subject': 'Raicho probe missing recipient'},
            'mode': 'sendNow',
        },
        timeout=15,
    )
    assert not invalid_api['ok'], invalid_api
    invalid_identity = client.command(
        'send',
        {
            'details': {
                **message_details('Raicho probe missing identity'),
                'identityId': 'missing',
            },
            'mode': 'sendNow',
        },
        timeout=15,
    )
    assert not invalid_identity['ok'], invalid_identity
    try:
        before = client.events()
        client.faults(smtp='reject')
        rejected_subject = 'Raicho probe SMTP rejection'
        rejected = send_message(client, rejected_subject)
        assert not rejected['ok'], rejected
        assert not client.messages(rejected_subject)
        rejected_events = verify_fault_events(
            before, client.events(), accepted=0, required=['smtp_rejected']
        )
    finally:
        client.faults()
    lost_subject = 'Raicho probe lost controller result'
    before = client.events()
    lost_result = send_message(client, lost_subject, drop_result=True)
    assert lost_result.get('outcome') == 'unknown', lost_result
    client.wait_connected()
    lost_messages = received_once(client, lost_subject)
    lost_events = verify_fault_events(before, client.events(), accepted=1)
    client.record(
        'faults',
        {
            'invalid_extension_input': invalid_extension,
            'invalid_api_input': invalid_api,
            'invalid_identity': invalid_identity,
            'smtp_rejected': rejected,
            'smtp_rejection_events': rejected_events,
            'lost_controller_result': lost_result,
            'lost_controller_delivery': lost_messages,
            'lost_controller_events': lost_events,
        },
    )
    try:
        before = client.events()
        client.faults(smtp='drop_ack')
        subject = 'Raicho probe lost SMTP acknowledgment'
        outcome = send_message(client, subject)
        received = received_once(client, subject)
        events = verify_fault_events(
            before, client.events(), accepted=1, required=['smtp_ack_dropped']
        )
        client.record(
            'smtp_lost_acknowledgment',
            {
                'api_response': outcome,
                'received': received,
                'fault_events': events,
                'interpretation': 'SMTP receipt is independent of the caller outcome. No resend attempted.',
            },
        )
    finally:
        client.faults()
    try:
        before = client.events()
        client.faults(imap='reject_sent_append')
        subject = 'Raicho probe Sent copy failure'
        outcome = send_message(client, subject)
        received = received_once(client, subject)
        sent_copies = client.messages(subject, folder='Sent', username='sender')
        assert not sent_copies, sent_copies
        events = verify_fault_events(
            before, client.events(), accepted=1, required=['sent_append_rejected']
        )
        client.record(
            'sent_copy_failure',
            {
                'api_response': outcome,
                'received': received,
                'sent_copies': sent_copies,
                'fault_events': events,
                'interpretation': 'Submission succeeded despite failed Sent storage. No resend attempted.',
            },
        )
    finally:
        client.faults()
