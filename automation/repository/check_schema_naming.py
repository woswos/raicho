"""Keep database schema names in snake_case by inspecting the schema migrations build."""

import re
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

from automation.paths import REPOSITORY_ROOT

SNAKE_CASE = re.compile(r'[a-z][a-z0-9]*(?:_[a-z0-9]+)*')
MIGRATIONS = Path('server/migrations')


def schema_names(connection):
    objects = connection.execute('SELECT type, name FROM sqlite_master ORDER BY type, name').fetchall()
    names = {(kind, name) for kind, name in objects if not name.startswith('sqlite_')}
    columns = {
        ('column', f'{table}.{column}')
        for kind, table in names
        if kind == 'table'
        for (column,) in connection.execute('SELECT name FROM pragma_table_xinfo(?)', (table,))
    }
    return names | columns


def check_schema_naming(root):
    root = Path(root).resolve()
    failures = []
    seen = set()
    with closing(sqlite3.connect(':memory:')) as connection:
        for migration in sorted((root / MIGRATIONS).glob('*.sql')):
            location = migration.relative_to(root).as_posix()
            try:
                connection.executescript(migration.read_text())
            except (OSError, UnicodeDecodeError, sqlite3.Error) as error:
                failures.append(f'{location}: cannot apply migration: {error}')
                break
            current = schema_names(connection)
            for kind, name in sorted(current - seen):
                checked = name.split('.', 1)[1] if kind == 'column' else name
                if not SNAKE_CASE.fullmatch(checked):
                    failures.append(f'{location}: {kind} {name} must use snake_case')
            seen |= current
    return failures


def main():
    if len(sys.argv) > 2:
        print('FAIL: expected at most one repository root argument', file=sys.stderr)
        return 1
    root = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else REPOSITORY_ROOT
    failures = check_schema_naming(root)
    for failure in failures:
        print(f'FAIL: {failure}', file=sys.stderr)
    if failures:
        return 1
    print('schema-naming check passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
