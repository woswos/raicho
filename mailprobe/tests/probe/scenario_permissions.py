def verify(client):
    observed = client.call('permission_status')
    assert observed.get('send_allowed') is True, (
        'Grant messages.send through the Thunderbird permission prompt before continuing.'
    )
    client.record(
        'send_permission',
        {
            'status': 'granted',
            'source': 'Thunderbird user consent',
            'observed': observed,
        },
    )


def record_skips(client):
    for name in ['delivery', 'native', 'faults']:
        client.record(
            name,
            {
                'status': 'not_run',
                'reason': (
                    'The unattended run checks drafts only. Run with --native for '
                    'Thunderbird messages.send consent, delivery, native editing, '
                    'and delivery fault scenarios.'
                ),
            },
        )
