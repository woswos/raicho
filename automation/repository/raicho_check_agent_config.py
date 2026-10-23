import re
import sys
from pathlib import Path

from automation.raicho_paths import REPOSITORY_ROOT

REQUIRED_IMPORTS = (
    'docs/contributing/working-agreement.md',
    'docs/contributing/workflow.md',
    'docs/reference/key-conventions.md',
    'docs/reference/architecture.md',
)


def citation_failures(root):
    failures = []
    for cited in re.findall(r'`([^`\n]+)`', (root / 'AGENTS.md').read_text()):
        if '/' not in cited or not cited.endswith('.md'):
            continue
        candidate = Path(cited)
        if candidate.is_absolute() or '..' in candidate.parts:
            failures.append(f'instruction reference escapes repository: {cited}')
            continue
        disk = root / candidate
        if not disk.resolve().is_relative_to(root):
            failures.append(f'instruction reference escapes repository: {cited}')
        elif disk.is_symlink():
            failures.append(f'instruction file must be a regular file: {cited}')
        elif not disk.is_file():
            failures.append(f'missing instruction file: {cited}')
    return failures


def check_agent_config(root):
    root = Path(root).resolve()
    failures = []
    visited = set()

    def inspect_imports(path, ancestors=()):
        path = path.resolve()
        if path in ancestors:
            failures.append(f'instruction import cycle: {path.relative_to(root)}')
            return
        if path in visited:
            return
        visited.add(path)
        if not path.is_file():
            failures.append(f'missing instruction file: {path.relative_to(root)}')
            return
        for line in path.read_text().splitlines():
            if not line.startswith('@'):
                continue
            target = (path.parent / line[1:]).resolve()
            if not target.is_relative_to(root):
                failures.append(f'instruction reference escapes repository: {line}')
            else:
                inspect_imports(target, (*ancestors, path))

    try:
        inspect_imports(root / 'AGENTS.md')
        for relative in REQUIRED_IMPORTS:
            if (root / relative).resolve() not in visited:
                failures.append(f'AGENTS.md must reference {relative}')
        if (root / 'AGENTS.md').is_file():
            failures.extend(citation_failures(root))
        skills = root / '.agents' / 'skills'
        if skills.is_symlink() or not skills.is_dir():
            failures.append('.agents/skills must be the canonical regular directory')
    except (OSError, ValueError, RuntimeError) as error:
        failures.append(str(error))
    return failures


def main():
    if len(sys.argv) > 2:
        print('FAIL: expected at most one repository root argument', file=sys.stderr)
        return 1
    root = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else REPOSITORY_ROOT
    failures = check_agent_config(root)
    for failure in failures:
        print(f'FAIL: {failure}', file=sys.stderr)
    if failures:
        return 1
    print('agent-config check passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
