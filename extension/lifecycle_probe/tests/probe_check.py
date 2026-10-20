import argparse
import json
import sys
import time
from pathlib import Path

from probe_files import write_json


def check_observations(
    observations: dict,
    expected_version: str,
    minimum_heartbeats: int,
    minimum_elapsed: float,
    *,
    now: float | None = None,
    baseline: dict | None = None,
    same_session: bool = False,
) -> dict:
    if observations['rejections']:
        raise ValueError('Fixture rejected a connection or message')
    timestamp = time.time() if now is None else now
    previous_sessions = {
        session['session_id'] for session in (baseline or {}).get('sessions', [])
    }
    sessions = observations['sessions']
    if not sessions:
        raise ValueError('No extension connection observed')
    session = sessions[-1]
    if (
        session['extension_version'] != expected_version
        or session['heartbeat_count'] < minimum_heartbeats
        or session['last_seen'] - session['first_seen'] < minimum_elapsed
        or timestamp - session['last_seen'] > 30
    ):
        raise ValueError('Latest session does not yet satisfy lifecycle evidence')
    if baseline is not None:
        if same_session and session['session_id'] not in previous_sessions:
            raise ValueError('Extension session changed during idle observation')
        if not same_session and session['session_id'] in previous_sessions:
            raise ValueError('No new extension session observed since baseline')
    return session


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, default=Path('/fixture'))
    parser.add_argument('--expected-version', required=True)
    parser.add_argument('--minimum-heartbeats', type=int, default=1)
    parser.add_argument('--minimum-elapsed', type=float, default=0)
    parser.add_argument('--timeout', type=float, default=120)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--same-session', action='store_true')
    parser.add_argument('--save-baseline', type=Path)
    arguments = parser.parse_args()
    if arguments.same_session and arguments.baseline is None:
        parser.error('--same-session requires --baseline')
    baseline = (
        json.loads(arguments.baseline.read_text()) if arguments.baseline else None
    )
    deadline = time.monotonic() + arguments.timeout
    while True:
        try:
            observations = json.loads(
                (arguments.directory / 'observations.json').read_text()
            )
            session = check_observations(
                observations,
                arguments.expected_version,
                arguments.minimum_heartbeats,
                arguments.minimum_elapsed,
                baseline=baseline,
                same_session=arguments.same_session,
            )
            break
        except (OSError, ValueError) as error:
            if time.monotonic() >= deadline:
                print(f'FAIL: {error}', file=sys.stderr)
                return 1
            time.sleep(min(1, max(0, deadline - time.monotonic())))
    if arguments.save_baseline:
        write_json(arguments.save_baseline, observations)
    print(
        f'Lifecycle check passed: extension {session["extension_version"]}, '
        f'Thunderbird {session["browser_version"]}, '
        f'{session["heartbeat_count"]} heartbeats, '
        f'{session["last_seen"] - session["first_seen"]:.1f}s observed, '
        f'Origin {session["origin"]!r}'
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())
