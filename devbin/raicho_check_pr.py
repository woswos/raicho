import re
import subprocess
import sys
from pathlib import Path

from raicho_check_changelog import check_pull_request_changelog
from raicho_check_design_link import check_design_reference
from raicho_pr_context import changed_paths, load_context, regular_file_in_change


def evaluate_pr(root):
    context = load_context(root)
    paths = changed_paths(context, root)
    if 'design' in context['labels']:
        if not paths:
            raise ValueError(
                'design PR needs a comparison base and at least one changed plan'
            )
        invalid = [
            path
            for path in paths
            if not re.fullmatch(
                r'docs/planning/active/\d{8}-[a-z0-9]+(?:-[a-z0-9]+)*\.md', path
            )
        ]
        if invalid:
            raise ValueError(
                'design PR changes non-planning paths: ' + ', '.join(invalid)
            )
        for path in paths:
            if not regular_file_in_change(context, path, root):
                raise ValueError(f'design PR path is not a regular document: {path}')
        print(
            'PR labeled design: planning-only diff verified, design-link guard exempt'
        )
    elif 'skip-design-check' in context['labels']:
        print('design-link: skipped via skip-design-check label')
    elif paths is not None and all(path.endswith('.md') for path in paths):
        irregular = [
            path for path in paths if not regular_file_in_change(context, path, root)
        ]
        if irregular:
            raise ValueError(
                'changed Markdown path is not a regular file: ' + ', '.join(irregular)
            )
        print('design-link: skipped, PR changes Markdown documentation only')
    else:
        path = check_design_reference(context, root)
        print(f'design-link check passed: {path}')
    check_pull_request_changelog(context, paths)


def main():
    if len(sys.argv) > 2:
        print('FAIL: expected at most one repository root argument', file=sys.stderr)
        return 1
    root = (
        Path(sys.argv[1]).resolve()
        if len(sys.argv) == 2
        else Path(__file__).resolve().parents[1]
    )
    try:
        evaluate_pr(root)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    print('pr-guards: all applicable guards passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
