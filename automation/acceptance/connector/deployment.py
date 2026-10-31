import json
import sys

EXPECTED_NETWORKS = {
    'raicho': {'application', 'connector-application'},
    'gateway': {'connector-application', 'connector-thunderbird'},
    'thunderbird': {'thunderbird', 'connector-thunderbird'},
}


def networks(container):
    project = container['Config']['Labels']['com.docker.compose.project']
    return {name.removeprefix(f'{project}_') for name in container['NetworkSettings']['Networks']}


def deployment():
    documents = json.load(sys.stdin)
    containers = {
        document['Config']['Labels']['com.docker.compose.service']: document
        for document in documents
        if 'Config' in document
    }
    internal = {
        document['Labels']['com.docker.compose.network']: document['Internal']
        for document in documents
        if 'Internal' in document
    }
    assert internal == {'connector-application': True, 'connector-thunderbird': True}, (
        'Connector networks must deny external routing and DNS forwarding'
    )
    gateway = containers['gateway']
    assert gateway['Config']['User'] == '10001:10001'
    assert gateway['HostConfig']['ReadonlyRootfs']
    assert gateway['HostConfig']['CapDrop'] == ['ALL']
    assert not gateway['HostConfig'].get('CapAdd')
    assert not gateway['HostConfig']['PortBindings']
    assert all(mount['Type'] == 'tmpfs' for mount in gateway['Mounts'])
    for service, expected in EXPECTED_NETWORKS.items():
        assert networks(containers[service]) == expected, service
    assert not networks(containers['raicho']) & networks(containers['thunderbird'])
    print('Only the gateway bridges Raicho and Thunderbird, and it has no ports, secrets or data mounts')
