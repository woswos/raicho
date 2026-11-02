import argparse
import json

from mailprobe.tests.probe import (
    scenario_delivery,
    scenario_drafts,
    scenario_faults,
    scenario_native,
    scenario_permissions,
    scenario_restart,
    scenario_settlement,
    scenario_synchronization,
)
from mailprobe.tests.probe.client import ProbeClient, wait_until
from mailprobe.tests.proxy.mail_inspect import ensure_mailboxes

SCENARIOS = {
    'drafts': scenario_drafts.run,
    'delivery': scenario_delivery.run,
    'restart': scenario_restart.run,
    'faults': scenario_faults.run,
    'settlement': scenario_settlement.run,
    'native_prepare': scenario_native.prepare,
    'native_verify': scenario_native.verify,
    'permission_verify': scenario_permissions.verify,
    'record_skips': scenario_permissions.record_skips,
    'synchronization_prepare': scenario_synchronization.prepare,
    'synchronization': scenario_synchronization.run,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'phase', choices=['prepare', 'inventory', 'evidence', 'command', 'synchronization_seed', *SCENARIOS]
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
    if arguments.phase == 'synchronization_seed':
        scenario_synchronization.seed(client)
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
    else:
        SCENARIOS[arguments.phase](client)


if __name__ == '__main__':
    main()
