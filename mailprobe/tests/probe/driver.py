import argparse
import importlib
import json

from mailprobe.tests.probe.client import ProbeClient, wait_until
from mailprobe.tests.proxy.mail_inspect import ensure_mailboxes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'phase',
        choices=[
            'prepare',
            'inventory',
            'drafts',
            'delivery',
            'restart',
            'faults',
            'settlement',
            'native_prepare',
            'native_verify',
            'permission_verify',
            'record_skips',
            'evidence',
            'command',
        ],
    )
    parser.add_argument('--action')
    parser.add_argument('--arguments', default='{}')
    arguments = parser.parse_args()
    client = ProbeClient()
    if arguments.phase == 'prepare':

        def prepared():
            try:
                ensure_mailboxes()
            except OSError:
                return None
            return True

        wait_until(prepared, 60, 'Fixture mailboxes did not become available.')
        return
    if arguments.phase == 'evidence':
        print(json.dumps(client.evidence(), indent=2))
        return
    metadata = client.wait_connected()
    if arguments.phase == 'inventory':
        client.record('runtime', metadata)
        print(json.dumps(client.call('inventory'), indent=2))
    elif arguments.phase == 'command':
        print(
            json.dumps(
                client.command(arguments.action, json.loads(arguments.arguments)),
                indent=2,
            )
        )
    elif arguments.phase.startswith('native_'):
        from mailprobe.tests.probe import scenario_native

        getattr(scenario_native, arguments.phase.removeprefix('native_'))(client)
    elif arguments.phase in ['permission_verify', 'record_skips']:
        from mailprobe.tests.probe import scenario_permissions

        function = 'verify' if arguments.phase == 'permission_verify' else 'record_skips'
        getattr(scenario_permissions, function)(client)
    else:
        module = importlib.import_module(f'mailprobe.tests.probe.scenario_{arguments.phase}')
        module.run(client)


if __name__ == '__main__':
    main()
