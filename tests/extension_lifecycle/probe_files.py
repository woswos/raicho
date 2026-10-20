import json
import os
import re
import secrets
import tempfile
from pathlib import Path


def write_json(path: Path, document: dict) -> None:
    with tempfile.NamedTemporaryFile(
        mode='w', dir=path.parent, prefix=f'.{path.name}.', delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
        try:
            os.chmod(temporary_path, 0o600)
            json.dump(document, temporary, sort_keys=True)
            temporary.write('\n')
            temporary.flush()
            os.replace(temporary_path, path)
        finally:
            temporary_path.unlink(missing_ok=True)


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
    with os.fdopen(descriptor, 'w') as secret_file:
        token = secrets.token_hex(32)
        secret_file.write(f'{token}\n')
    return token
