import json

from raicho_guard_fixtures import GuardTestCase

DESIGN = 'docs/planning/active/20261018-test-design.md'
CODE_CHANGE = {'devbin/tool.py': 'print("example")\n'}


class PullRequestLabelTests(GuardTestCase):
    def check_labels(self, repo, environment, labels):
        return self.run_guard(
            repo,
            'raicho_check_pr.py',
            {**environment, 'PR_LABELS': labels, 'PR_DESCRIPTION': ''},
        )

    def test_design_label_accepts_planning_only_changes(self):
        repo, environment = self.pull_request({DESIGN: '# Design\n'})
        result = self.check_labels(repo, environment, 'design')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('planning-only diff verified', result.stdout)

    def test_design_label_needs_a_comparison_base(self):
        repo, environment = self.pull_request({DESIGN: '# Design\n'})
        environment.pop('PR_BASE_SHA')
        result = self.check_labels(repo, environment, 'design')
        self.assertEqual(result.returncode, 1)
        self.assertIn('design PR needs a comparison base', result.stderr)

    def test_skip_label_does_not_bypass_design_path_restrictions(self):
        repo, environment = self.pull_request({**CODE_CHANGE, DESIGN: '# Design\n'})
        result = self.check_labels(repo, environment, 'design,skip-design-check')
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            'design PR changes non-planning paths: devbin/tool.py', result.stderr
        )

    def test_skip_label_exempts_an_implementation_reference(self):
        repo, environment = self.pull_request(CODE_CHANGE)
        result = self.check_labels(repo, environment, 'skip-design-check')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('skipped via skip-design-check label', result.stdout)

    def test_design_label_rejects_a_plan_symlink(self):
        repo, environment = self.pull_request({DESIGN: '# Design\n'})
        (repo.root / DESIGN).unlink()
        (repo.root / DESIGN).symlink_to('../../../README.md')
        repo.commit()
        environment['PR_HEAD_SHA'] = repo.head()
        result = self.check_labels(repo, environment, 'design')
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            f'design PR path is not a regular document: {DESIGN}', result.stderr
        )

    def test_github_event_takes_precedence_over_local_skip_label(self):
        repo, environment = self.pull_request(CODE_CHANGE)
        event_path = repo.root / 'event.json'
        repo.write(
            'event.json',
            json.dumps(
                {
                    'pull_request': {
                        'body': None,
                        'labels': [],
                        'base': {'sha': environment['PR_BASE_SHA']},
                        'head': {'sha': environment['PR_HEAD_SHA']},
                    }
                }
            ),
        )
        environment['GITHUB_EVENT_PATH'] = str(event_path)
        environment['PR_BASE_SHA'] = 'invalid-local-value'
        environment['PR_HEAD_SHA'] = 'invalid-local-value'
        result = self.check_labels(repo, environment, 'skip-design-check')
        self.assertEqual(result.returncode, 1)
        self.assertIn('exactly one standalone Design: or Decision:', result.stderr)
