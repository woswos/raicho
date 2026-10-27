import json
import time
import urllib.request
from pathlib import Path

from mailprobe.tests.proxy.fault_state import write_json
from mailprobe.tests.proxy.mail_inspect import inspect_messages


def wait_until(attempt, timeout, failure):
    deadline = time.monotonic() + timeout
    while (result := attempt()) is None:
        if time.monotonic() > deadline:
            raise AssertionError(failure)
        time.sleep(1)
    return result


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
        def metadata():
            status = self.request('status')
            return status['metadata'] if status['connected'] else None

        return wait_until(metadata, 90, 'Mail probe did not connect.')

    def command(self, action, arguments=None, timeout=120, drop_result=False, request_timeout=190):
        return self.request(
            'command',
            {
                'action': action,
                'arguments': arguments or {},
                'timeout': timeout,
                'drop_result': drop_result,
            },
            timeout=request_timeout,
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
            message for message in inspect_messages(folder=folder, username=username) if message['subject'] == subject
        ]

    def wait_messages(self, subject, count, folder='INBOX', username='recipient'):
        def messages():
            found = self.messages(subject, folder, username)
            return found if len(found) == count else None

        return wait_until(messages, 30, f'{subject}: expected {count} in {folder}')

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
