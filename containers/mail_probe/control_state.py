import threading
import time
import uuid

from probe_files import read_token


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
            if (
                self.pending is None
                or message.get('id') != self.pending['command']['id']
            ):
                return True
            if self.pending['drop_result']:
                self.disconnect(session)
                return False
            self.pending['response'] = message
            self.condition.notify_all()
            return True
