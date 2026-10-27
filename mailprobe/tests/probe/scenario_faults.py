from mailprobe.tests.probe.scenario_delivery import (
    message_details,
    received_once,
    send_message,
)
from mailprobe.tests.probe.scenario_helpers import (
    LOST_ACKNOWLEDGMENT_SUBJECT,
    LOST_RESULT_SUBJECT,
    MISSING_IDENTITY_SUBJECT,
    MISSING_RECIPIENT_SUBJECT,
    REJECTED_SUBJECT,
    SENT_COPY_FAILURE_SUBJECT,
)


def verify_fault_events(before, after, *, accepted, required=()):
    counters = set(before) | set(after) | {'smtp_accepted'} | set(required)
    delta = {name: after.get(name, 0) - before.get(name, 0) for name in counters}
    assert all(value >= 0 for value in delta.values()), delta
    assert delta['smtp_accepted'] == accepted, delta
    assert all(delta[name] >= 1 for name in required), delta
    return delta


def run(client):
    invalid = {}
    for name, details in (
        ('invalid_extension_input', {'subject': 123}),
        ('invalid_api_input', {'subject': MISSING_RECIPIENT_SUBJECT}),
        ('invalid_identity', {**message_details(MISSING_IDENTITY_SUBJECT), 'identityId': 'missing'}),
    ):
        response = client.command('send', {'details': details, 'mode': 'sendNow'}, timeout=15)
        assert not response['ok'], response
        invalid[name] = response
    try:
        before = client.events()
        client.faults(smtp='reject')
        rejected = send_message(client, REJECTED_SUBJECT)
        assert not rejected['ok'], rejected
        assert not client.messages(REJECTED_SUBJECT)
        rejected_events = verify_fault_events(before, client.events(), accepted=0, required=['smtp_rejected'])
    finally:
        client.faults()
    before = client.events()
    lost_result = send_message(client, LOST_RESULT_SUBJECT, drop_result=True)
    assert lost_result.get('outcome') == 'unknown', lost_result
    client.wait_connected()
    lost_messages = received_once(client, LOST_RESULT_SUBJECT)
    lost_events = verify_fault_events(before, client.events(), accepted=1)
    client.record(
        'faults',
        {
            **invalid,
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
        outcome = send_message(client, LOST_ACKNOWLEDGMENT_SUBJECT)
        received = received_once(client, LOST_ACKNOWLEDGMENT_SUBJECT)
        events = verify_fault_events(before, client.events(), accepted=1, required=['smtp_ack_dropped'])
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
        outcome = send_message(client, SENT_COPY_FAILURE_SUBJECT)
        received = received_once(client, SENT_COPY_FAILURE_SUBJECT)
        sent_copies = client.messages(SENT_COPY_FAILURE_SUBJECT, folder='Sent', username='sender')
        assert not sent_copies, sent_copies
        events = verify_fault_events(before, client.events(), accepted=1, required=['sent_append_rejected'])
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
