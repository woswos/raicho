import json
import os
import socket
import stat
import sys
from pathlib import Path


def main():
    if os.getuid() != 10001:
        raise ValueError('Thunderbird must run as UID 10001.')
    runtime = Path('/tmp/raicho-runtime')
    policy_path = Path('/opt/thunderbird/distribution/policies.json')
    if (
        not policy_path.is_symlink()
        or policy_path.resolve() != runtime / 'policies.json'
    ):
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
    process_names = {process['name'] for process in processes}
    if process_names.intersection({'vnc', 'browser-admin'}):
        raise ValueError('The lifecycle test must not start desktop administration.')
    for port in (5900, 6080):
        with socket.socket() as connection:
            connection.settimeout(1)
            if connection.connect_ex(('127.0.0.1', port)) == 0:
                raise ValueError(
                    'An administrative listener is unexpectedly available.'
                )
    sentinel = Path('/config/profile/raicho_lifecycle_sentinel')
    if sys.argv[1:] == ['seed']:
        sentinel.write_text('disposable lifecycle profile\n')
    elif sys.argv[1:] == ['persist']:
        if sentinel.read_text() != 'disposable lifecycle profile\n':
            raise ValueError('The disposable profile was not preserved.')
    elif sys.argv[1:]:
        raise ValueError('Expected seed, persist, or no argument.')
    print('Runtime passed: UID 10001, private symlinked policy, viewer disabled.')


if __name__ == '__main__':
    main()
