import json
import re
import sys
from pathlib import Path

from automation.paths import REPOSITORY_ROOT

SKILL_NAME = r'[a-z0-9]+(?:-[a-z0-9]+)*'


def scalar(value):
    value = value.strip()
    if not value:
        raise ValueError('empty scalar')
    if value.startswith('"'):
        parsed = json.loads(value)
        if not isinstance(parsed, str):
            raise ValueError('expected a quoted string')
        return parsed
    if value.startswith("'"):
        if not re.fullmatch(r"'(?:[^']|'')*'", value):
            raise ValueError('malformed single-quoted scalar')
        return value[1:-1].replace("''", "'")
    if value[0] in '|>!&*[]{},#%@`' or ': ' in value or ' #' in value:
        raise ValueError('unsupported YAML syntax, use a quoted single-line scalar')
    if value in {'null', 'true', 'false', '~'} or re.fullmatch(
        r'[-+]?\d+(?:\.\d+)?', value
    ):
        raise ValueError('expected a string scalar')
    return value


def inspect_skill(root, directory):
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError('skills root must contain only regular skill directories')
    if not re.fullmatch(SKILL_NAME, directory.name):
        raise ValueError('invalid skill directory name')
    entries = list(directory.iterdir())
    path = directory / 'SKILL.md'
    if entries != [path] or path.is_symlink() or not path.is_file():
        raise ValueError('each flat skill directory must contain only SKILL.md')
    lines = path.read_text().splitlines()
    if not lines or lines[0] != '---':
        raise ValueError('missing YAML frontmatter opening delimiter')
    try:
        closing = lines.index('---', 1)
    except ValueError:
        raise ValueError('missing YAML frontmatter closing delimiter') from None
    metadata = {}
    examples = []
    reading_examples = False
    for line in lines[1:closing]:
        if not line.strip():
            continue
        if reading_examples and line.startswith('  - '):
            examples.append(scalar(line[4:]))
            continue
        reading_examples = False
        match = re.fullmatch(r'(name|description|examples):(?: (.*))?', line)
        if not match or match[1] in metadata:
            raise ValueError('unsupported or duplicate frontmatter field')
        key, value = match[1], match[2] or ''
        if key == 'examples':
            if value or not directory.name.startswith('add-'):
                raise ValueError('examples must be a block list on an add-* skill')
            metadata[key] = examples
            reading_examples = True
        else:
            metadata[key] = scalar(value)
    if metadata.get('name') != directory.name:
        raise ValueError('frontmatter name must match directory')
    if not metadata.get('description', '').strip():
        raise ValueError('description must be a nonempty string')
    if directory.name.startswith('add-') and not 1 <= len(examples) <= 3:
        raise ValueError('add-* skills need one to three examples')
    body = '\n'.join(lines[closing + 1 :])
    for example in examples:
        original = root / example
        target = original.resolve()
        if (
            original.is_symlink()
            or Path(example).is_absolute()
            or not target.is_relative_to(root)
            or not target.is_file()
        ):
            raise ValueError(f'example is not an existing repository file: {example}')
        if example not in body:
            raise ValueError(f'example must be cited in the skill body: {example}')


def check_skills(root):
    root = Path(root)
    failures = []
    try:
        directories = sorted((root / '.agents' / 'skills').iterdir())
        if not directories:
            failures.append('shared skills directory is empty')
        for directory in directories:
            try:
                inspect_skill(root, directory)
            except (OSError, ValueError) as error:
                failures.append(f'{directory.name}: {error}')
    except OSError as error:
        failures.append(str(error))
    return failures


def main():
    if len(sys.argv) > 2:
        print('FAIL: expected at most one repository root argument', file=sys.stderr)
        return 1
    root = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else REPOSITORY_ROOT
    failures = check_skills(root)
    for failure in failures:
        print(f'FAIL: {failure}', file=sys.stderr)
    if failures:
        return 1
    print('skills check passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
