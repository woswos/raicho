import json
import subprocess
import sys
from pathlib import Path

from thunderbird_supervisor import process_identity


def healthy(state_path=Path('/tmp/raicho-runtime/processes.json')):
    try:
        identities = json.loads(state_path.read_text())
        names = {identity['name'] for identity in identities}
        if not {'dbus', 'display', 'window-manager', 'thunderbird'} <= names:
            return False
        for identity in identities:
            started = process_identity(identity['pid'])
            if started is None or started != identity['started']:
                return False
        return (
            subprocess.run(
                ['xdpyinfo', '-display', ':99'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2,
                check=False,
            ).returncode
            == 0
        )
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired):
        return False


if __name__ == '__main__':
    sys.exit(0 if healthy() else 1)
