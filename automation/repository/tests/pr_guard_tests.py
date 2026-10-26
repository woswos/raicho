from automation.testing.guard_fixtures import GuardTestCase


class PullRequestGuardTests(GuardTestCase):
    def test_regular_markdown_change_skips_design_link(self):
        repo = self.repo()
        repo.write('README.md', 'base\n')
        repo.commit()
        base = repo.head()
        repo.write('docs/guide.md', 'more\n')
        repo.commit()
        result = self.run_guard(
            repo,
            'check_pr.py',
            {
                'PR_BASE_SHA': base,
                'PR_HEAD_SHA': repo.head(),
                'PR_DESCRIPTION': '',
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Markdown documentation only', result.stdout)

    def test_deleted_regular_markdown_stays_exempt(self):
        repo = self.repo()
        repo.write('docs/guide.md', 'base\n')
        repo.commit()
        base = repo.head()
        (repo.root / 'docs' / 'guide.md').unlink()
        repo.commit()
        result = self.run_guard(
            repo,
            'check_pr.py',
            {
                'PR_BASE_SHA': base,
                'PR_HEAD_SHA': repo.head(),
                'PR_DESCRIPTION': '',
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_markdown_symlink_does_not_skip_design_link(self):
        repo = self.repo()
        repo.write('README.md', 'base\n')
        repo.commit()
        base = repo.head()
        (repo.root / 'notes.md').symlink_to('README.md')
        repo.commit()
        result = self.run_guard(
            repo,
            'check_pr.py',
            {
                'PR_BASE_SHA': base,
                'PR_HEAD_SHA': repo.head(),
                'PR_DESCRIPTION': '',
            },
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('changed Markdown path is not a regular file: notes.md', result.stderr)

    def test_code_change_still_requires_a_reference(self):
        repo = self.repo()
        repo.write('README.md', 'base\n')
        repo.commit()
        base = repo.head()
        repo.write('automation/tool.py', 'x\n')
        repo.commit()
        result = self.run_guard(
            repo,
            'check_pr.py',
            {
                'PR_BASE_SHA': base,
                'PR_HEAD_SHA': repo.head(),
                'PR_DESCRIPTION': '',
            },
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('exactly one standalone Design: or Decision:', result.stderr)

    def test_invalid_decision_date_names_the_path(self):
        repo = self.repo()
        repo.write('README.md', 'x\n')
        repo.commit()
        result = self.run_guard(
            repo,
            'check_design_link.py',
            {
                'PR_HEAD_SHA': repo.head(),
                'PR_DESCRIPTION': 'Decision: docs/decisions/20261340-bad-date.md',
            },
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            'FAIL: invalid date prefix: docs/decisions/20261340-bad-date.md',
            result.stderr,
        )


if __name__ == '__main__':
    import unittest

    unittest.main()
