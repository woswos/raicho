import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from raicho_check_agent_config import REQUIRED_IMPORTS

REPOSITORY = Path(__file__).resolve().parents[1]
DEVBIN = Path(__file__).resolve().parent
CLEARED_ENVIRONMENT = (
    'GITHUB_EVENT_PATH',
    'PR_DESCRIPTION',
    'PR_LABELS',
    'PR_BASE_SHA',
    'PR_HEAD_SHA',
)


class TemporaryRepo:
    def __init__(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.email', 'guards@example.com')
        self.git('config', 'user.name', 'Guard Tests')
        hooks = self.root / '.githooks'
        hooks.mkdir()
        self.git('config', 'core.hooksPath', str(hooks))
        self.git('config', 'commit.gpgsign', 'false')

    def git(self, *arguments):
        subprocess.run(
            ['git', *arguments],
            cwd=self.root,
            check=True,
            capture_output=True,
        )

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self, message='test'):
        self.git('add', '-A')
        self.git('commit', '-q', '-m', message)

    def head(self):
        completed = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=self.root,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )
        return completed.stdout.strip()

    def cleanup(self):
        self.directory.cleanup()


class GuardTestCase(unittest.TestCase):
    def repo(self):
        temporary = TemporaryRepo()
        self.addCleanup(temporary.cleanup)
        return temporary

    def instructions(self):
        repo = self.repo()
        citation = 'docs/contributing/git-and-pull-requests.md'
        lines = ['# Test', '']
        lines.extend(f'@{item}' for item in REQUIRED_IMPORTS)
        lines.extend(['', f'- Git: `{citation}`', ''])
        repo.write('AGENTS.md', '\n'.join(lines))
        for item in (*REQUIRED_IMPORTS, citation):
            repo.write(item, 'ok\n')
        (repo.root / '.agents' / 'skills').mkdir(parents=True)
        return repo

    def run_guard(self, repo, script, extra):
        command = ['python3', '-B', str(DEVBIN / script), str(repo.root)]
        return self.run_command(command, repo.root, extra)

    def install_guards(self, repo):
        directory = repo.root / 'devbin'
        directory.mkdir(exist_ok=True)
        for source in (
            *DEVBIN.glob('raicho_check_*.py'),
            DEVBIN / 'raicho_changelog.py',
            DEVBIN / 'raicho_pr_context.py',
            DEVBIN / 'raicho_shell_shebang.py',
            DEVBIN / 'raicho_version.py',
            DEVBIN / 'raicho_version_lock.py',
        ):
            shutil.copy2(source, directory / source.name)

    def run_guard_cli(self, repo, script, extra, directory, arguments=()):
        command = ['python3', '-B', str(repo.root / 'devbin' / script), *arguments]
        return self.run_command(command, directory, extra)

    def pull_request(self, changes, base_files=None):
        repo = self.repo()
        repo.write('README.md', 'base\n')
        for path, content in (base_files or {}).items():
            repo.write(path, content)
        repo.commit()
        base = repo.head()
        for path, content in changes.items():
            if content is None:
                (repo.root / path).unlink()
            else:
                repo.write(path, content)
        repo.commit()
        return repo, {'PR_BASE_SHA': base, 'PR_HEAD_SHA': repo.head()}

    def run_command(self, command, directory, extra):
        environment = os.environ.copy()
        for name in CLEARED_ENVIRONMENT:
            environment.pop(name, None)
        environment.update(extra)
        return subprocess.run(
            command,
            cwd=directory,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
