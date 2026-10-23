"""Fail when a user-visible change has no changelog entry.

The entry belongs in the pull request description, where it is reviewed with
the change, or under Unreleased in CHANGELOG.md. Refactors, tests, docs, and
tooling do not need one. The "no changelog" label is the escape hatch when an
operator would notice nothing.
"""

import subprocess
import sys
from pathlib import Path

from automation.raicho_paths import REPOSITORY_ROOT
from automation.release.raicho_changelog import parse_description_entries
from automation.repository.raicho_pr_context import changed_paths, load_context


def is_shipping(path):
    name = path.rsplit('/', 1)[-1]
    if '/tests/' in f'/{path}' or name.endswith(('_tests.py', '_test.rs')):
        return False
    if '.test.' in name or name.endswith('.dockerignore'):
        return False
    if path.startswith('server/src/') and name.endswith('.rs'):
        return True
    if path.startswith(('server/queries/', 'server/migrations/')) and name.endswith(
        '.sql'
    ):
        return True
    if path.startswith('web/src/') and name.endswith(('.ts', '.css')):
        return True
    if path.startswith('protocol/typescript/src/') and name.endswith(('.ts', '.js')):
        return True
    if path.startswith('web/public/') and name.endswith(('.html', '.css', '.svg')):
        return True
    if path.startswith('extension/') and (
        name == 'manifest.json' or name.endswith(('.ts', '.html', '.css'))
    ):
        return True
    if path.startswith(
        (
            'containers/raicho/',
            'containers/thunderbird/',
            'runtime/thunderbird/',
            'runtime/credentials/',
        )
    ):
        return True
    return False


def check_pull_request_changelog(context, paths):
    if 'no changelog' in context['labels']:
        print('changelog: skipped via no changelog label')
        return
    if paths is None:
        print('changelog: skipped, no comparison base')
        return
    shipping = [path for path in paths if is_shipping(path)]
    if not shipping:
        print('changelog: no shipping change')
        return
    if 'CHANGELOG.md' in paths:
        print('changelog: CHANGELOG.md was updated')
        return
    if parse_description_entries(context['description']):
        print('changelog: description has an entry')
        return
    listed = '\n'.join(f'  {path}' for path in shipping)
    raise ValueError(
        'This change touches code that ships and has no changelog entry:\n'
        f'{listed}\n'
        'Fill in the Changelog block of the description, or add an entry under '
        '"## [Unreleased]" in CHANGELOG.md.\n'
        'If an operator would notice nothing, add the "no changelog" label.'
    )


def main():
    if len(sys.argv) > 2:
        print('FAIL: expected at most one repository root argument', file=sys.stderr)
        return 1
    root = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else REPOSITORY_ROOT
    try:
        context = load_context(root)
        check_pull_request_changelog(context, changed_paths(context, root))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
