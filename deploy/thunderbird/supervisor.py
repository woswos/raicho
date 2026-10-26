import json
import os
import signal
import subprocess
import time
from pathlib import Path


def process_identity(process_id):
    try:
        fields = Path(f'/proc/{process_id}/stat').read_text().rsplit(')', 1)[1].split()
        return None if fields[0] == 'Z' else fields[19]
    except FileNotFoundError:
        return None


def signal_process(process, signal_number):
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal_number)
        except ProcessLookupError:
            process.wait()


def finish_process(process, timeout):
    try:
        process.wait(timeout=max(0, timeout))
    except subprocess.TimeoutExpired:
        signal_process(process, signal.SIGKILL)
        process.wait()


class Supervisor:
    def __init__(self, state_path):
        self.state_path = state_path
        self.children = []
        self.stopping = False

    def request_stop(self, _signal_number, _frame):
        self.stopping = True

    def start(self, name, arguments):
        # Thunderbird's native output may include private mail or account details.
        output = subprocess.DEVNULL if name == 'thunderbird' else None
        process = subprocess.Popen(arguments, start_new_session=True, stdout=output, stderr=output)
        self.children.append((name, process))
        print(f'Started {name}.', flush=True)

    def publish(self):
        identities = [
            {'name': name, 'pid': process.pid, 'started': process_identity(process.pid)}
            for name, process in self.children
        ]
        temporary = self.state_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(identities))
        temporary.replace(self.state_path)

    def wait_for(self, ready, timeout=20):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and not self.stopping:
            self.require_running()
            if ready():
                return
            time.sleep(0.1)
        raise RuntimeError('A required service did not become ready.')

    def require_running(self):
        for name, process in self.children:
            if process.poll() is not None:
                raise RuntimeError(f'{name} exited with status {process.returncode}.')

    def monitor(self):
        while not self.stopping:
            try:
                self.require_running()
            except RuntimeError as error:
                print(f'FAIL: {error}', flush=True)
                return 1
            time.sleep(0.2)
        return 0

    def stop(self):
        self.state_path.unlink(missing_ok=True)
        deadline = time.monotonic() + 20
        for name, process in self.children:
            if name == 'thunderbird':
                signal_process(process, signal.SIGTERM)
                finish_process(process, min(15, deadline - time.monotonic()))
        remaining = [process for name, process in self.children if name != 'thunderbird']
        for process in remaining:
            signal_process(process, signal.SIGTERM)
        for process in remaining:
            finish_process(process, deadline - time.monotonic())
