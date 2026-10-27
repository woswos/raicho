from mailprobe.tests.probe.scenario_helpers import ATTACHMENT, ATTACHMENT_SHA256

SUBJECT = 'Raicho probe native edited'
BODY = 'Edited through the native Thunderbird interface.'


def prepare(client):
    baseline = client.read_record('drafts')['native_target']
    matches = client.call(
        'query',
        {
            'query': {
                'headerMessageId': baseline['headerMessageId'],
                'folderId': baseline['folder']['id'],
            }
        },
    )['messages']
    assert len(matches) == 1, matches
    selected = matches[0]
    client.call('select_draft', {'message_id': selected['id']})
    client.record('native_baseline', selected)
    print("Use Thunderbird's Edit button on the selected draft.")
    print(f'Change Subject to: {SUBJECT}')
    print(f'Replace the body with: {BODY}')
    print('Verify alias@raicho.test and probe.txt remain. Press Ctrl+S and leave the compose window open.')


def verify(client):
    baseline = client.read_record('native_baseline')
    tabs = client.call('inspect_native_compose')
    matches = [entry for entry in tabs if entry['details']['subject'] == SUBJECT]
    assert len(matches) == 1, tabs
    current = matches[0]
    assert current['details']['type'] == 'draft', current
    assert current['details']['identityId'] == client.read_record('drafts')['identity']['id'], current
    messages = client.wait_messages(SUBJECT, 1, folder='Drafts', username='sender')
    originals = client.messages(baseline['subject'], folder='Drafts', username='sender')
    assert not originals, originals
    message = messages[0]
    assert 'alias@raicho.test' in message['from'], message
    assert BODY in message['plain'] or BODY in message['html'], message
    assert any(
        part['filename'] == ATTACHMENT['name'] and part['sha256'] == ATTACHMENT_SHA256
        for part in message['attachments']
    ), message
    client.record(
        'native_interoperability',
        {
            'compose': current,
            'stored': message,
            'original_subject_count': len(originals),
            'replacement_count': len(messages),
            'method': 'Native UI Edit action, edit Subject/body, Ctrl+S. API inspection only.',
        },
    )
    client.call('close_compose', {'tab_id': current['tab']['id']})
