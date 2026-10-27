from mailprobe.tests.probe.scenario_helpers import (
    ATTACHMENT,
    message_parts,
    save_native_target,
    saved_message,
    wait_query,
)


def run(client):
    inventory = client.call('inventory')
    assert inventory['api']['saveMessage'] == 'function', inventory
    identities = [identity for account in inventory['accounts'] for identity in account.get('identities', [])]
    secondary = next(identity for identity in identities if identity['email'] == 'alias@raicho.test')
    client.record('inventory', inventory)
    details = {
        'identityId': secondary['id'],
        'to': ['recipient@raicho.test'],
        'subject': 'Raicho probe plain draft',
        'plainTextBody': 'Raicho plain fixture body.',
        'isPlainText': True,
    }
    plain = saved_message(client, details)
    plain_content = client.call('get_message', {'message_id': plain['id']})
    assert secondary['email'] in plain_content['header']['author'], plain_content
    assert any('Raicho plain fixture body.' in part.get('body', '') for part in message_parts(plain_content['full'])), (
        plain_content
    )
    repeated = saved_message(client, details)
    repeated_messages = wait_query(client, details['subject'], 2)
    assert repeated['id'] != plain['id'], repeated_messages

    html = saved_message(
        client,
        {
            'identityId': secondary['id'],
            'to': ['recipient@raicho.test'],
            'subject': 'Raicho probe HTML draft',
            'body': '<p>Raicho <strong>HTML fixture</strong>.</p>',
            'deliveryFormat': 'html',
            'attachments': [ATTACHMENT],
        },
    )
    html_content = client.call('get_message', {'message_id': html['id']})
    assert secondary['email'] in html_content['header']['author'], html_content
    assert any(
        part.get('contentType') == 'text/html' and '<strong>HTML fixture</strong>' in part.get('body', '')
        for part in message_parts(html_content['full'])
    ), html_content
    assert any(
        attachment['name'] == ATTACHMENT['name'] and attachment['content'] == ATTACHMENT['content']
        for attachment in html_content['attachments']
    ), html_content

    reopened = client.call('begin_new', {'message_id': plain['id']})
    assert reopened['details']['type'] == 'new', reopened
    tab_identifier = reopened['tab']['id']
    edited_subject = 'Raicho probe edited as new'
    client.call(
        'update_compose',
        {
            'tab_id': tab_identifier,
            'details': {
                'subject': edited_subject,
                'body': '<p>First edited fixture body.</p>',
            },
        },
    )
    first_save = client.call('save_compose', {'tab_id': tab_identifier})
    wait_query(client, details['subject'], 2)
    first_saved_messages = wait_query(client, edited_subject, 1, body='First edited fixture body.')
    client.call(
        'update_compose',
        {
            'tab_id': tab_identifier,
            'details': {
                'body': '<p>Second edited fixture body.</p>',
            },
        },
    )
    second_save = client.call('save_compose', {'tab_id': tab_identifier})
    saved_edit = wait_query(client, edited_subject, 1, body='Second edited fixture body.')
    stale_lookup = client.command(
        'get_message',
        {
            'message_id': first_saved_messages[0]['id'],
        },
        timeout=15,
    )
    client.call('close_compose', {'tab_id': tab_identifier})
    native_target = save_native_target(client, details)
    client.record(
        'drafts',
        {
            'identity': secondary,
            'plain': plain,
            'html': html,
            'repeated': repeated,
            'duplicate_count': len(repeated_messages),
            'plain_content': plain_content,
            'html_content': html_content,
            'edit_as_new': reopened,
            'first_compose_save': first_save,
            'second_compose_save': second_save,
            'same_tab_count': len(saved_edit),
            'stale_compose_message_lookup': stale_lookup,
            'native_target': native_target,
        },
    )
