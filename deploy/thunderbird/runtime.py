import os
import signal
import subprocess
import sys
from pathlib import Path

from .policy import write_policies
from .supervisor import Supervisor


def admin_enabled(value):
    if value not in ('', 'false', 'true'):
        raise ValueError('RAICHO_ADMIN_ENABLED must be true or false.')
    return value == 'true'


def commands(administration):
    selected = {
        'dbus': [
            'dbus-daemon',
            '--session',
            '--nofork',
            '--address=unix:path=/tmp/raicho-runtime/bus',
        ],
        'display': ['Xvfb', ':99', '-screen', '0', '1280x800x24', '-nolisten', 'tcp'],
        'window-manager': ['openbox', '--sm-disable'],
        'thunderbird': [
            '/opt/thunderbird/thunderbird',
            '-no-remote',
            '-profile',
            '/config/profile',
        ],
    }
    if administration:
        selected['vnc'] = [
            'x11vnc',
            '-display',
            ':99',
            '-localhost',
            '-rfbport',
            '5900',
            '-forever',
            '-shared',
            '-nopw',
            '-quiet',
        ]
        selected['browser-admin'] = [
            'websockify',
            '--web',
            '/usr/share/novnc',
            '6080',
            '127.0.0.1:5900',
        ]
    return selected


def display_ready():
    return (
        subprocess.run(
            ['xdpyinfo', '-display', ':99'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=2,
        ).returncode
        == 0
    )


def main():
    runtime_directory = Path('/tmp/raicho-runtime')
    supervisor = Supervisor(runtime_directory / 'processes.json')
    for signal_number in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signal_number, supervisor.request_stop)
    try:
        write_policies(runtime_directory, Path('/opt/raicho/extension'), os.environ)
        supervisor.state_path.unlink(missing_ok=True)
        (runtime_directory / 'bus').unlink(missing_ok=True)
        selected = commands(
            admin_enabled(os.environ.get('RAICHO_ADMIN_ENABLED', 'false'))
        )
        Path('/config/profile').mkdir(mode=0o700, parents=True, exist_ok=True)
        for name, arguments in selected.items():
            supervisor.start(name, arguments)
            if name == 'dbus':
                supervisor.wait_for(lambda: (runtime_directory / 'bus').exists())
            elif name == 'display':
                supervisor.wait_for(display_ready)
        supervisor.publish()
        return supervisor.monitor()
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f'FAIL: Thunderbird startup failed: {error}', file=sys.stderr, flush=True)
        return 1
    finally:
        supervisor.stop()


if __name__ == '__main__':
    sys.exit(main())
