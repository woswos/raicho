import os
import re
import secrets
import threading
import time
import uuid
from pathlib import Path


def read_token(directory: Path) -> str:
    path = directory / 'token'
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        if path.is_symlink() or path.stat().st_mode & 0o077:
            raise ValueError('Fixture token must be a private regular file') from None
        token = path.read_text().strip()
        if not re.fullmatch('[0-9a-f]{64}', token):
            raise ValueError('Fixture token has an invalid format') from None
        return token
    with os.fdopen(descriptor, 'w') as token_file:
        token = secrets.token_hex(32)
        token_file.write(f'{token}\n')
    return token


class ControlState:
    def __init__(self, directory):
        self.token = read_token(directory)
        self.condition = threading.Condition()
        self.session = None
        self.metadata = None
        self.pending = None

    def connect(self, session, browser_version, extension_version):
        with self.condition:
            if self.session is not None:
                self.disconnect(self.session)
            self.session = str(uuid.uuid4())
            self.metadata = {
                'session_id': session,
                'browser_version': browser_version,
                'extension_version': extension_version,
            }
            self.condition.notify_all()
            return self.session

    def disconnect(self, session):
        with self.condition:
            if self.session != session:
                return
            self.session = None
            if self.pending is not None and self.pending['response'] is None:
                self.pending['response'] = {
                    'ok': False,
                    'outcome': 'unknown',
                    'error': 'Probe disconnected.',
                }
            self.condition.notify_all()

    def status(self):
        with self.condition:
            return {'connected': self.session is not None, 'metadata': self.metadata}

    def submit(self, action, arguments, timeout=120, drop_result=False):
        with self.condition:
            if self.session is None or self.pending is not None:
                raise ValueError('Probe unavailable or busy.')
            command = {
                'id': str(uuid.uuid4()),
                'action': action,
                'arguments': arguments,
            }
            pending = {
                'command': command,
                'issued': False,
                'response': None,
                'drop_result': drop_result,
            }
            self.pending = pending
            deadline = time.monotonic() + timeout
            try:
                while pending['response'] is None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return {
                            'ok': False,
                            'outcome': 'unknown',
                            'error': 'Probe result timed out.',
                        }
                    self.condition.wait(remaining)
                return pending['response']
            finally:
                self.pending = None

    def next_command(self, session):
        with self.condition:
            if (
                self.session != session
                or self.pending is None
                or self.pending['issued']
                or self.pending['response'] is not None
            ):
                return None
            self.pending['issued'] = True
            return self.pending['command']

    def finish(self, session, message):
        with self.condition:
            if self.session != session:
                raise ValueError('Result came from an inactive probe.')
            if self.pending is None or message.get('id') != self.pending['command']['id']:
                return True
            if self.pending['drop_result']:
                self.disconnect(session)
                return False
            self.pending['response'] = message
            self.condition.notify_all()
            return True
