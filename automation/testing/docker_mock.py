import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

EXECUTABLE = """#!/usr/bin/env python3
import json
import os
import signal
import sys
from pathlib import Path

directory = Path(__file__).resolve().parent
arguments = sys.argv[1:]
with (directory / 'trace').open('a') as trace:
    trace.write(json.dumps(arguments) + '\\n')
configuration = json.loads((directory / 'responses.json').read_text())
for response in configuration['responses']:
    if set(response['words']) <= set(arguments):
        sys.stdout.write(response['output'])
        sys.stderr.write(response['error'])
        if response['terminate_parent']:
            os.kill(os.getppid(), signal.SIGTERM)
        raise SystemExit(response['status'])
raise SystemExit(configuration['status'])
"""


@dataclass
class Response:
    words: tuple
    status: int = 0
    output: str = ''
    error: str = ''
    terminate_parent: bool = False


class DockerMock:
    def __init__(self, directory, responses=(), status=0):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory / 'responses.json').write_text(
            json.dumps(
                {
                    'status': status,
                    'responses': [asdict(response) for response in responses],
                }
            )
        )
        executable = self.directory / 'docker'
        executable.write_text(EXECUTABLE)
        executable.chmod(0o700)

    def environment(self, **variables):
        return os.environ | {'PATH': f'{self.directory}:{os.environ["PATH"]}'} | variables

    def commands(self):
        trace = self.directory / 'trace'
        if not trace.exists():
            return []
        return [json.loads(line) for line in trace.read_text().splitlines()]
