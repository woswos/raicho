import json
import os
import re
import subprocess


def git_output(*arguments, root):
    return subprocess.check_output(
        ['git', *arguments], stderr=subprocess.PIPE, cwd=root
    )


def commit_sha(value, name, root):
    if not isinstance(value, str) or not re.fullmatch(
        r'[0-9a-fA-F]{40}|[0-9a-fA-F]{64}', value
    ):
        raise ValueError(f'{name} must be a full commit SHA')
    try:
        git_output('cat-file', '-e', f'{value}^{{commit}}', root=root)
    except subprocess.CalledProcessError:
        raise ValueError(f'{name} commit is unavailable locally: {value}') from None
    return value


def load_context(root):
    event_path = os.environ.get('GITHUB_EVENT_PATH')
    if event_path:
        event = json.loads((root / event_path).read_text())
        pull_request = event.get('pull_request') if isinstance(event, dict) else None
        if not isinstance(pull_request, dict):
            raise ValueError('GitHub event has no pull_request object')
        description = pull_request.get('body')
        description = '' if description is None else description
        label_items = pull_request.get('labels')
        if not isinstance(label_items, list) or any(
            not isinstance(label, dict) or not isinstance(label.get('name'), str)
            for label in label_items
        ):
            raise ValueError('GitHub event labels must be objects with string names')
        labels = [label['name'] for label in label_items]
        base = pull_request.get('base')
        head = pull_request.get('head')
        if not isinstance(base, dict) or not isinstance(head, dict):
            raise ValueError('GitHub event is missing base/head metadata')
        base_sha = commit_sha(base.get('sha'), 'PR base', root)
        head_sha = commit_sha(head.get('sha'), 'PR head', root)
    else:
        description = os.environ.get('PR_DESCRIPTION', '')
        labels = [
            label.strip()
            for label in os.environ.get('PR_LABELS', '').split(',')
            if label.strip()
        ]
        base_value = os.environ.get('PR_BASE_SHA', '')
        base_sha = commit_sha(base_value, 'PR base', root) if base_value else None
        head_value = (
            os.environ.get('PR_HEAD_SHA')
            or git_output('rev-parse', 'HEAD', root=root).decode().strip()
        )
        head_sha = commit_sha(head_value, 'PR head', root)
    if not isinstance(description, str):
        raise ValueError('PR description must be a string or null')
    return {
        'description': description,
        'labels': set(labels),
        'base': base_sha,
        'head': head_sha,
    }


def changed_paths(context, root):
    if context['base'] is None:
        return None
    comparison = f'{context["base"]}...{context["head"]}'
    output = git_output(
        'diff', '--name-only', '-z', '--no-renames', comparison, '--', root=root
    )
    return [os.fsdecode(path) for path in output.split(b'\0') if path]


def description_references(description):
    references = []
    fence = None
    in_comment = False
    for line in description.splitlines():
        if fence:
            if re.fullmatch(
                re.escape(fence[0]) + '{' + str(len(fence)) + r',}\s*', line.strip()
            ):
                fence = None
            continue
        if not in_comment and line.startswith(('    ', '\t')):
            continue
        visible = ''
        remaining = line
        while remaining:
            if in_comment:
                closing = remaining.find('-->')
                if closing < 0:
                    break
                remaining = remaining[closing + 3 :]
                in_comment = False
            else:
                opening = remaining.find('<!--')
                if opening < 0:
                    visible += remaining
                    break
                visible += remaining[:opening]
                remaining = remaining[opening + 4 :]
                in_comment = True
        stripped = visible.strip()
        marker = re.match(r'^(`{3,}|~{3,})', stripped)
        if marker:
            fence = marker[1]
            continue
        match = re.fullmatch(r'(Design|Decision):[ \t]*(.*)', stripped)
        if match:
            references.append((match[1], match[2].strip()))
    return references


def regular_file_at(commit, path, root):
    output = git_output('ls-tree', '-z', commit, '--', path, root=root)
    entries = [entry for entry in output.split(b'\0') if entry]
    if len(entries) != 1:
        return False
    metadata, name = entries[0].split(b'\t', 1)
    mode, kind, object_id = metadata.split()
    return (
        os.fsdecode(name) == path and mode in {b'100644', b'100755'} and kind == b'blob'
    )


def regular_file_in_change(context, path, root):
    commit = (
        context['head']
        if git_output('ls-tree', context['head'], '--', path, root=root)
        else context['base']
    )
    if commit is None:
        return False
    return regular_file_at(commit, path, root)
