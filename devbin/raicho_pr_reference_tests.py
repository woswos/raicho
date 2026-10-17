from raicho_guard_fixtures import GuardTestCase

DESIGN = 'docs/planning/active/20261018-test-design.md'
DECISION = 'docs/decisions/20261018-test-decision.md'
CODE_CHANGE = {'devbin/tool.py': 'print("example")\n'}


class PullRequestReferenceTests(GuardTestCase):
    def check_reference(self, repo, environment, description):
        return self.run_guard(
            repo,
            'raicho_check_pr.py',
            {**environment, 'PR_DESCRIPTION': description},
        )

    def test_design_is_resolved_at_base_even_when_deleted_at_head(self):
        repo, environment = self.pull_request(
            {**CODE_CHANGE, DESIGN: None}, {DESIGN: '# Design\n'}
        )
        result = self.check_reference(repo, environment, f'Design: {DESIGN}')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f'design-link check passed: {DESIGN}', result.stdout)

    def test_design_added_only_at_head_is_rejected(self):
        repo, environment = self.pull_request({**CODE_CHANGE, DESIGN: '# Design\n'})
        result = self.check_reference(repo, environment, f'Design: {DESIGN}')
        self.assertEqual(result.returncode, 1)
        self.assertIn('target commit (merge the design first)', result.stderr)

    def test_decision_can_be_introduced_at_head(self):
        repo, environment = self.pull_request({**CODE_CHANGE, DECISION: '# Decision\n'})
        result = self.check_reference(repo, environment, f'Decision: {DECISION}')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f'design-link check passed: {DECISION}', result.stdout)

    def test_decision_deleted_at_head_is_rejected(self):
        repo, environment = self.pull_request(
            {**CODE_CHANGE, DECISION: None}, {DECISION: '# Decision\n'}
        )
        result = self.check_reference(repo, environment, f'Decision: {DECISION}')
        self.assertEqual(result.returncode, 1)
        self.assertIn('not a regular file at the PR head commit', result.stderr)

    def test_design_requires_a_comparison_base(self):
        repo, environment = self.pull_request(CODE_CHANGE, {DESIGN: '# Design\n'})
        environment.pop('PR_BASE_SHA')
        result = self.check_reference(repo, environment, f'Design: {DESIGN}')
        self.assertEqual(result.returncode, 1)
        self.assertIn('Design lookup requires PR_BASE_SHA', result.stderr)

    def test_examples_and_comments_do_not_count_as_references(self):
        repo, environment = self.pull_request({**CODE_CHANGE, DECISION: '# Decision\n'})
        description = '\n'.join(
            [
                '```markdown',
                f'Design: {DESIGN}',
                '```',
                '<!--',
                f'Design: {DESIGN}',
                '-->',
                f'    Design: {DESIGN}',
                f'Decision: {DECISION}',
            ]
        )
        result = self.check_reference(repo, environment, description)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_multiple_standalone_references_are_rejected(self):
        repo, environment = self.pull_request(
            {**CODE_CHANGE, DECISION: '# Decision\n'}, {DESIGN: '# Design\n'}
        )
        result = self.check_reference(
            repo, environment, f'Design: {DESIGN}\nDecision: {DECISION}'
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn('exactly one standalone Design: or Decision:', result.stderr)
