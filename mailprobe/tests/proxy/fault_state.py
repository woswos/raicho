import json
import os
import tempfile
import threading
from pathlib import Path

MODES = {
    'smtp': {'normal', 'reject', 'drop_ack'},
    'imap': {'normal', 'reject_sent_append'},
}


def write_json(path: Path, document: dict) -> None:
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
        try:
            json.dump(document, temporary, sort_keys=True)
            temporary.write('\n')
            temporary.flush()
            os.replace(temporary_path, path)
        finally:
            temporary_path.unlink(missing_ok=True)


class FaultState:
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.settings_path = directory / 'faults.json'
        self.events_path = directory / 'fault_events.json'
        self.lock = threading.Lock()
        if not self.settings_path.exists():
            write_json(self.settings_path, dict.fromkeys(MODES, 'normal'))
        self.events = {}
        if self.events_path.exists():
            self.events = json.loads(self.events_path.read_text())
        write_json(self.events_path, self.events)

    def setting(self, name: str) -> str:
        settings = json.loads(self.settings_path.read_text())
        if set(settings) != set(MODES) or any(mode not in MODES[protocol] for protocol, mode in settings.items()):
            raise ValueError('Invalid fixture fault settings')
        return settings[name]

    def record(self, event: str) -> None:
        with self.lock:
            self.events[event] = self.events.get(event, 0) + 1
            write_json(self.events_path, self.events)
