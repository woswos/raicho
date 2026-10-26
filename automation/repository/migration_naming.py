import re
from pathlib import Path

MIGRATION_DIRECTORY = Path('server/migrations')
MIGRATION_NAME = re.compile(r'(?P<version>[0-9]{4})_[a-z][a-z0-9]*(?:_[a-z0-9]+)*\.sql')


def migration_failures(paths):
    failures = []
    versions = {}
    for path in paths:
        if path.parent != MIGRATION_DIRECTORY or path.suffix.lower() != '.sql':
            continue
        match = MIGRATION_NAME.fullmatch(path.name)
        if match is None:
            failures.append(
                f'{path} must use a four-digit sequence and snake_case description: 0000_descriptive_name.sql'
            )
            continue
        version = match.group('version')
        if version in versions:
            failures.append(f'duplicate migration version {version}: {versions[version]} and {path}')
        else:
            versions[version] = path
    return failures
