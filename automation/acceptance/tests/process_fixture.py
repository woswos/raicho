import os
import signal
import time
from pathlib import Path


def start_time(process):
    try:
        status = Path(f'/proc/{process}/stat').read_text()
    except FileNotFoundError:
        return '0'
    return status.rsplit(') ', 1)[1].split()[19]


def stopped(process):
    for _ in range(100):
        try:
            state = Path(f'/proc/{process}/stat').read_text().rsplit(') ', 1)[1].split()[0]
        except FileNotFoundError:
            return True
        if state == 'Z':
            return True
        time.sleep(0.1)
    return False


def kill(process):
    try:
        os.kill(process, signal.SIGKILL)
    except ProcessLookupError:
        pass
