import time

from mailprobe.tests.probe.scenario_helpers import DELIVERED_SUBJECTS, UNDELIVERED_SUBJECTS

OBSERVATION_SECONDS = 30


def run(client):
    time.sleep(OBSERVATION_SECONDS)
    received = {}
    for subject in DELIVERED_SUBJECTS:
        messages = client.messages(subject)
        assert len(messages) == 1, {'subject': subject, 'messages': messages}
        received[subject] = len(messages)
    undelivered = {subject: len(client.messages(subject)) for subject in UNDELIVERED_SUBJECTS}
    assert not any(undelivered.values()), undelivered
    events = client.events()
    assert events['smtp_accepted'] == len(DELIVERED_SUBJECTS), events
    client.record(
        'settlement',
        {
            'observation_seconds': OBSERVATION_SECONDS,
            'recipient_counts': received,
            'fault_events': events,
            'queued_and_rejected_deliveries': sum(undelivered.values()),
        },
    )
