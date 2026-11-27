import re
from pathlib import Path

CREDENTIALS = re.compile(r'LOGIN|AUTHENTICATE', re.IGNORECASE)
LINE_LIMIT = 3000


def redacted(lines):
    return [line for line in lines if not CREDENTIALS.search(line)]


def main():
    for path in sorted(Path('/config').glob('thunderbird-log*')):
        lines = redacted(path.read_text(errors='replace').splitlines())
        print(f'Thunderbird log {path.name}, last {min(len(lines), LINE_LIMIT)} of {len(lines)} lines:')
        print('\n'.join(lines[-LINE_LIMIT:]))


if __name__ == '__main__':
    main()
