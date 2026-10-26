import subprocess
import tempfile
from pathlib import Path

import yaml
from raicho_guard_fixtures import GuardTestCase

WORKFLOWS = Path(__file__).resolve().parents[1] / '.github/workflows'


class ReleasePushTests(GuardTestCase):
    def prepare_remote(self, reject_tags):
        repo = self.repo()
        for name in ('Cargo.toml', 'Cargo.lock', 'CHANGELOG.md'):
            repo.write(name, '0.1.0\n')
        repo.commit()
        base = repo.head()
        directory = tempfile.TemporaryDirectory(prefix='raicho-release-remote-')
        self.addCleanup(directory.cleanup)
        remote = Path(directory.name)
        subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
        repo.git('remote', 'add', 'origin', str(remote))
        repo.git('push', '-q', 'origin', 'HEAD:main')
        if reject_tags:
            hook = remote / 'hooks/update'
            hook.write_text('#!/bin/sh\ncase "$1" in refs/tags/*) exit 1;; esac\n')
            hook.chmod(0o700)
        for name in ('Cargo.toml', 'Cargo.lock', 'CHANGELOG.md'):
            repo.write(name, '0.1.1\n')
        return repo, remote, base

    def run_push_step(self, workflow_name, repo):
        workflow = yaml.safe_load((WORKFLOWS / workflow_name).read_text())
        step = next(
            step
            for step in workflow['jobs']['cut']['steps']
            if step.get('name') == 'Commit and tag'
        )
        script = step['run'].replace('${{ steps.cut.outputs.tag }}', 'v0.1.1')
        return subprocess.run(
            ['bash', '--noprofile', '--norc', '-e', '-o', 'pipefail', '-c', script],
            cwd=repo.root,
            capture_output=True,
            text=True,
            check=False,
        )

    def remote_commit(self, remote, ref):
        return subprocess.check_output(
            ['git', '--git-dir', str(remote), 'rev-parse', ref + '^{commit}'],
            text=True,
        ).strip()

    def test_tag_rejection_leaves_main_unchanged(self):
        for workflow in ('auto-release.yml', 'major-release.yml'):
            with self.subTest(workflow=workflow):
                repo, remote, base = self.prepare_remote(reject_tags=True)
                result = self.run_push_step(workflow, repo)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('hook declined to update refs/tags/v0.1.1', result.stderr)
                self.assertEqual(self.remote_commit(remote, 'main'), base)
                tags = subprocess.check_output(
                    ['git', '--git-dir', str(remote), 'tag', '--list'], text=True
                )
                self.assertEqual(tags, '')

    def test_success_publishes_main_and_tag_at_same_commit(self):
        for workflow in ('auto-release.yml', 'major-release.yml'):
            with self.subTest(workflow=workflow):
                repo, remote, base = self.prepare_remote(reject_tags=False)
                result = self.run_push_step(workflow, repo)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                released = self.remote_commit(remote, 'main')
                self.assertNotEqual(released, base)
                self.assertEqual(self.remote_commit(remote, 'v0.1.1'), released)
