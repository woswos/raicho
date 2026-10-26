from automation.paths import REPOSITORY_ROOT
from automation.repository.check_doc_naming import (
    check_doc_naming,
    filename_failure,
)
from automation.testing.guard_fixtures import GuardTestCase


class DocNamingTests(GuardTestCase):
    def test_live_repository_names_pass(self):
        self.assertEqual(check_doc_naming(REPOSITORY_ROOT), [])

    def test_accepted_document_layout(self):
        names = [
            'docs/planning/active/20261018-plan.md',
            'docs/planning/done/20261018-plan.md',
            'docs/planning/template.md',
            'docs/planning/active/template.md',
            'docs/decisions/20261018-record.md',
            'docs/decisions/template.md',
            'docs/decisions/README.md',
            'docs/contributing/workflow.md',
        ]
        for name in names:
            self.assertIsNone(filename_failure(name), name)

    def test_plan_outside_active_or_done_fails(self):
        name = 'docs/planning/20261018-misplaced.md'
        self.assertEqual(
            filename_failure(name),
            f'planning document must be template.md or a dated file in active/ or done/: {name}',
        )

    def test_nested_decision_fails(self):
        name = 'docs/decisions/nested/20261018-record.md'
        self.assertEqual(
            filename_failure(name),
            f'decision record must be template.md or a dated file in docs/decisions/: {name}',
        )

    def test_invalid_plan_date_names_the_path(self):
        name = 'docs/planning/active/20261340-bad-date.md'
        self.assertEqual(filename_failure(name), f'invalid date prefix: {name}')

    def test_missing_worktree_file_keeps_its_filename_check(self):
        repo = self.repo()
        repo.write('docs/Bad Name.md', 'x\n')
        repo.commit()
        (repo.root / 'docs' / 'Bad Name.md').unlink()
        self.assertEqual(
            check_doc_naming(repo.root),
            ['invalid documentation filename: docs/Bad Name.md'],
        )

    def test_missing_valid_file_is_not_a_naming_failure(self):
        repo = self.repo()
        repo.write('docs/contributing/workflow.md', 'x\n')
        repo.commit()
        (repo.root / 'docs' / 'contributing' / 'workflow.md').unlink()
        self.assertEqual(check_doc_naming(repo.root), [])

    def test_document_symlink_is_rejected(self):
        repo = self.repo()
        repo.write('docs/contributing/workflow.md', 'x\n')
        repo.commit()
        link = repo.root / 'docs' / 'planning' / 'active' / '20261018-link.md'
        link.parent.mkdir(parents=True)
        link.symlink_to(repo.root / 'docs' / 'contributing' / 'workflow.md')
        repo.commit()
        self.assertEqual(
            check_doc_naming(repo.root),
            ['documentation must be a regular file: docs/planning/active/20261018-link.md'],
        )


if __name__ == '__main__':
    import unittest

    unittest.main()
