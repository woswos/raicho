import time


def run(client):
    time.sleep(30)
    received = {}
    for subject in [
        'Raicho probe immediate send',
        'Raicho probe lost controller result',
        'Raicho probe lost SMTP acknowledgment',
        'Raicho probe Sent copy failure',
    ]:
        messages = client.messages(subject)
        assert len(messages) == 1, {'subject': subject, 'messages': messages}
        received[subject] = len(messages)
    for subject in [
        'Raicho probe queued send',
        'Raicho probe SMTP rejection',
        'Raicho probe missing identity',
        'Raicho probe missing recipient',
    ]:
        assert not client.messages(subject), subject
    events = client.events()
    assert events['smtp_accepted'] == 4, events
    client.record(
        'settlement',
        {
            'observation_seconds': 30,
            'recipient_counts': received,
            'fault_events': events,
            'queued_and_rejected_deliveries': 0,
        },
    )
