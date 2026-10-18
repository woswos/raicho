import json
import time
import urllib.request
from pathlib import Path

from fault_state import write_json
from mail_inspect import inspect_messages


class ProbeClient:
    def __init__(self, directory=Path('/config')):
        self.directory = directory
        self.token = (directory / 'token').read_text().strip()

    def request(self, path, payload=None, timeout=190):
        request = urllib.request.Request(
            f'http://probe:8765/{path}',
            data=None if payload is None else json.dumps(payload).encode(),
            headers={
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json',
            },
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)

    def wait_connected(self):
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            status = self.request('status')
            if status['connected']:
                return status['metadata']
            time.sleep(1)
        raise AssertionError('Mail probe did not connect.')

    def command(self, action, arguments=None, timeout=120, drop_result=False):
        return self.request(
            'command',
            {
                'action': action,
                'arguments': arguments or {},
                'timeout': timeout,
                'drop_result': drop_result,
            },
        )

    def call(self, action, arguments=None):
        response = self.command(action, arguments)
        assert response['ok'], response
        return response['result']

    def faults(self, smtp='normal', imap='normal'):
        write_json(self.directory / 'faults.json', {'smtp': smtp, 'imap': imap})

    def events(self):
        return json.loads((self.directory / 'fault_events.json').read_text())

    def messages(self, subject, folder='INBOX', username='recipient'):
        return [
            message
            for message in inspect_messages(folder=folder, username=username)
            if message['subject'] == subject
        ]

    def wait_messages(self, subject, count, folder='INBOX', username='recipient'):
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            messages = self.messages(subject, folder, username)
            if len(messages) == count:
                return messages
            time.sleep(1)
        raise AssertionError(f'{subject}: expected {count}, found {len(messages)}')

    def record(self, name, data):
        path = self.directory / 'evidence.json'
        evidence = json.loads(path.read_text()) if path.exists() else {}
        evidence[name] = data
        write_json(path, evidence)
        print(f'Recorded {name}', flush=True)

    def evidence(self):
        return json.loads((self.directory / 'evidence.json').read_text())

    def read_record(self, name):
        return self.evidence()[name]
