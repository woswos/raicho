import json
import os
import socket
import stat
import sys
import time
from pathlib import Path

PROFILE = Path('/config/profile')
SENTINEL = PROFILE / 'raicho_acceptance_sentinel'


def check_runtime():
    if os.getuid() != 10001:
        raise ValueError('Thunderbird must run as UID 10001.')
    runtime = Path('/tmp/raicho-runtime')
    policy_path = Path('/opt/thunderbird/distribution/policies.json')
    if not policy_path.is_symlink() or policy_path.resolve() != runtime / 'policies.json':
        raise ValueError('The image policy must link to the runtime policy.')
    if stat.S_IMODE(runtime.stat().st_mode) != 0o700:
        raise ValueError('The runtime directory must have mode 0700.')
    if stat.S_IMODE(policy_path.stat().st_mode) != 0o600:
        raise ValueError('The runtime policy must have mode 0600.')
    policies = json.loads(policy_path.read_text())['policies']
    if policies['DisableAppUpdate'] is not True:
        raise ValueError('Application updates must remain disabled.')
    extension = policies['ExtensionSettings']['connector@raicho']
    if extension['installation_mode'] != 'force_installed':
        raise ValueError('The extension must be force installed.')
    if extension['updates_disabled'] is not True:
        raise ValueError('Extension background updates must remain disabled.')
    processes = json.loads((runtime / 'processes.json').read_text())
    if {process['name'] for process in processes} & {'vnc', 'browser-admin'}:
        raise ValueError('The check must not start desktop administration.')
    for port in (5900, 6080):
        with socket.socket() as connection:
            connection.settimeout(1)
            if connection.connect_ex(('127.0.0.1', port)) == 0:
                raise ValueError('An administrative listener is unexpectedly available.')


def installed_version():
    try:
        addons = json.loads((PROFILE / 'extensions.json').read_text())['addons']
    except (OSError, ValueError, KeyError):
        return None
    for addon in addons:
        if addon.get('id') == 'connector@raicho' and addon.get('active') is True:
            return addon.get('version')
    return None


def wait_for_version(expected):
    deadline = time.monotonic() + 30
    while installed_version() != expected:
        if time.monotonic() > deadline:
            raise ValueError(f'The profile did not activate connector {expected}.')
        time.sleep(1)


def main(arguments):
    check_runtime()
    if arguments == ['seed']:
        SENTINEL.write_text('disposable acceptance profile\n')
    elif arguments[:1] == ['persist'] and len(arguments) <= 2:
        if SENTINEL.read_text() != 'disposable acceptance profile\n':
            raise ValueError('The disposable profile was not preserved.')
        if len(arguments) == 2:
            wait_for_version(arguments[1])
    elif arguments:
        raise ValueError('Expected seed, persist, or persist with a version.')
    print('Thunderbird passed: UID 10001, private policy, no viewer, same profile.')


if __name__ == '__main__':
    main(sys.argv[1:])
