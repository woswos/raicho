import time


def request_before_deadline(client, action, arguments, deadline):
    remaining = deadline - time.monotonic()
    assert remaining > 0, 'Restarted fixture message did not become queryable.'
    response = client.request(
        'command',
        {
            'action': action,
            'arguments': arguments,
            'timeout': min(10, remaining),
            'drop_result': False,
        },
        timeout=remaining,
    )
    assert response['ok'], response
    return response['result']


def wait_for_identity(client, baseline):
    identity = {
        'headerMessageId': baseline['headerMessageId'],
        'folderId': baseline['folder']['id'],
    }
    deadline = time.monotonic() + 30
    initial_matches = None
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        matches = request_before_deadline(
            client, 'query', {'query': identity}, deadline
        )['messages']
        assert len(matches) <= 1, {'identity': identity, 'matches': matches}
        if initial_matches is None:
            initial_matches = matches
            if not matches:
                request_before_deadline(
                    client,
                    'select_folder',
                    {'folder_id': identity['folderId']},
                    deadline,
                )
        if matches:
            return matches, {
                'initial_matches': initial_matches,
                'folder_selection_required': not initial_matches,
            }
        time.sleep(min(1, max(0, deadline - time.monotonic())))
    raise AssertionError(
        f'Restarted fixture message did not become queryable: {identity}'
    )


def run(client):
    metadata = client.wait_connected()
    drafts = client.read_record('drafts')
    delivery = client.evidence().get('delivery')
    found = {}
    for name in ('plain', 'html', 'native_target'):
        baseline = drafts[name]
        matches, recovery = wait_for_identity(client, baseline)
        found[name] = {
            **recovery,
            'before': baseline,
            'after': matches[0],
            'content': client.call('get_message', {'message_id': matches[0]['id']}),
        }
    queued = {'status': 'not_run', 'reason': 'No delivery baseline exists.'}
    queued_recovery = queued
    if delivery and delivery.get('status') != 'not_run':
        queued, queued_recovery = wait_for_identity(client, delivery['queued_message'])
        assert not client.messages(delivery['queued_subject'])
    client.record(
        'restart',
        {
            'metadata': metadata,
            'drafts': found,
            'queued': queued,
            'queued_recovery': queued_recovery,
            'identity_rule': 'Resolve again by folder and RFC Message-ID, not the old numeric API identifier.',
        },
    )
