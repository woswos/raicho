import hmac
import json
import re
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit

from probe_files import read_token, write_json

METADATA_FIELDS = {'extension_version', 'browser_version', 'session_id'}


def parse_message(payload: str | bytes, expected_type: str) -> dict:
    if len(payload) > 4096:
        raise ValueError('Fixture message exceeded its size limit')
    try:
        if isinstance(payload, bytes):
            payload = payload.decode('utf-8')
        message = json.loads(payload)
    except (ValueError, UnicodeError):
        raise ValueError('Fixture message must be JSON') from None
    fields = METADATA_FIELDS | {'type', 'sequence'}
    if expected_type == 'lifecycle_probe':
        fields.add('token')
    if not isinstance(message, dict) or set(message) != fields:
        raise ValueError('Unexpected fixture message fields')
    if message['type'] != expected_type or type(message['sequence']) is not int:
        raise ValueError('Invalid fixture message type or sequence')
    for field in ['extension_version', 'browser_version']:
        if not isinstance(message[field], str) or not re.fullmatch(
            r'[0-9]+(?:\.[0-9]+){1,3}[a-z0-9.]*', message[field]
        ):
            raise ValueError('Invalid fixture version')
    if not isinstance(message['session_id'], str) or not re.fullmatch(
        r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', message['session_id']
    ):
        raise ValueError('Invalid fixture session identifier')
    return message


def safe_origin(origin: str | None) -> str | None:
    if origin is None or origin == 'null':
        return origin
    parsed = urlsplit(origin)
    if (
        len(origin) > 256
        or parsed.scheme not in {'moz-extension', 'http', 'https'}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {'', '/'}
    ):
        raise ValueError('Unexpected fixture Origin header')
    return origin


class ProbeState:
    def __init__(self, directory: Path):
        self.path = directory / 'observations.json'
        self.token = read_token(directory)
        self.lock = threading.Lock()
        self.observations = {'sessions': [], 'rejections': 0}
        if self.path.exists():
            self.observations = json.loads(self.path.read_text())
        write_json(self.path, self.observations)

    def snapshot(self) -> dict:
        with self.lock:
            return json.loads(json.dumps(self.observations))

    def reject(self) -> None:
        with self.lock:
            self.observations['rejections'] += 1
            write_json(self.path, self.observations)

    def connect(
        self, payload: str | bytes, origin: str | None, *, now: float | None = None
    ) -> str:
        message = parse_message(payload, 'lifecycle_probe')
        token = message['token']
        if (
            not isinstance(token, str)
            or not re.fullmatch('[0-9a-f]{64}', token)
            or not hmac.compare_digest(token, self.token)
            or message['sequence'] != 0
        ):
            raise ValueError('Fixture authentication failed')
        origin = safe_origin(origin)
        timestamp = time.time() if now is None else now
        with self.lock:
            sessions = self.observations['sessions']
            previous = next(
                (
                    session
                    for session in sessions
                    if session['session_id'] == message['session_id']
                ),
                None,
            )
            if previous is not None:
                if any(previous[field] != message[field] for field in METADATA_FIELDS):
                    raise ValueError('Reconnected fixture session changed identity')
                previous.update(sequence=0, last_seen=timestamp)
                previous['connection_count'] += 1
            else:
                if len(sessions) >= 128:
                    raise ValueError('Fixture session limit reached')
                sessions.append(
                    {field: message[field] for field in METADATA_FIELDS}
                    | {
                        'origin': origin,
                        'sequence': 0,
                        'heartbeat_count': 0,
                        'connection_count': 1,
                        'first_seen': timestamp,
                        'last_seen': timestamp,
                    }
                )
            write_json(self.path, self.observations)
        return message['session_id']

    def heartbeat(
        self, session_id: str, payload: str | bytes, *, now: float | None = None
    ) -> None:
        message = parse_message(payload, 'lifecycle_heartbeat')
        with self.lock:
            session = next(
                session
                for session in self.observations['sessions']
                if session['session_id'] == session_id
            )
            if any(message[field] != session[field] for field in METADATA_FIELDS) or (
                message['sequence'] != session['sequence'] + 1
            ):
                raise ValueError('Fixture heartbeat identity or sequence changed')
            session['sequence'] = message['sequence']
            session['heartbeat_count'] += 1
            session['last_seen'] = time.time() if now is None else now
            write_json(self.path, self.observations)
