import json
import os

from raicho_guard_fixtures import GuardTestCase

GUARDS = ('agent_config', 'doc_naming', 'skills', 'design_link', 'pr')
DECISION = 'docs/decisions/20261018-test-decision.md'


class GuardCliTests(GuardTestCase):
    def cli_repository(self):
        repo = self.instructions()
        self.install_guards(repo)
        repo.write(
            '.agents/skills/test/SKILL.md',
            '---\nname: test\ndescription: Test skill.\n---\n# Test\n',
        )
        repo.write(DECISION, '# Decision\n')
        repo.commit()
        return repo

    def assert_result(self, actual, expected, status):
        self.assertEqual(actual.returncode, status, actual.stderr)
        self.assertEqual(actual.returncode, expected.returncode)
        self.assertEqual(actual.stdout, expected.stdout)
        self.assertEqual(actual.stderr, expected.stderr)

    def test_default_root_uses_the_script_repository_from_another_directory(self):
        repo = self.cli_repository()
        caller = self.repo()
        caller.write('AGENTS.md', '# Missing instructions\n')
        caller.write('docs/Bad Name.md', '# Invalid\n')
        environment = {
            'PR_HEAD_SHA': repo.head(),
            'PR_DESCRIPTION': f'Decision: {DECISION}',
        }
        for guard in GUARDS:
            with self.subTest(guard=guard):
                script = f'raicho_check_{guard}.py'
                expected = self.run_guard(repo, script, environment)
                result = self.run_guard_cli(repo, script, environment, caller.root)
                self.assert_result(result, expected, 0)
                self.assertTrue(result.stdout)
                self.assertEqual(result.stderr, '')

    def test_default_root_preserves_failure_diagnostics_and_exit_codes(self):
        caller = self.repo()
        failures = {
            'agent_config': ('AGENTS.md', '# Missing instructions\n'),
            'doc_naming': ('docs/Bad Name.md', '# Invalid\n'),
            'skills': ('.agents/skills/test/SKILL.md', '# Missing frontmatter\n'),
            'design_link': None,
            'pr': None,
        }
        for guard, mutation in failures.items():
            with self.subTest(guard=guard):
                repo = self.cli_repository()
                if mutation:
                    repo.write(*mutation)
                environment = {'PR_HEAD_SHA': repo.head(), 'PR_DESCRIPTION': ''}
                script = f'raicho_check_{guard}.py'
                expected = self.run_guard(repo, script, environment)
                result = self.run_guard_cli(repo, script, environment, caller.root)
                self.assert_result(result, expected, 1)
                self.assertEqual(result.stdout, '')
                self.assertIn('FAIL:', result.stderr)

    def test_explicit_absolute_and_relative_roots_override_the_script_repository(self):
        repo = self.cli_repository()
        source = self.cli_repository()
        source.write('AGENTS.md', '# Invalid default root\n')
        source.write('docs/Bad Name.md', '# Invalid\n')
        source.write('.agents/skills/test/SKILL.md', '# Missing frontmatter\n')
        caller = self.repo()
        repo.write(
            '.agents/skills/add-test/SKILL.md',
            '---\nname: add-test\ndescription: Test example.\nexamples:\n'
            f'  - {DECISION}\n---\nSee `{DECISION}`.\n',
        )
        repo.commit()
        environment = {
            'PR_HEAD_SHA': repo.head(),
            'PR_DESCRIPTION': f'Decision: {DECISION}',
        }
        for guard in GUARDS:
            script = f'raicho_check_{guard}.py'
            expected = self.run_guard(repo, script, environment)
            for root in (str(repo.root), os.path.relpath(repo.root, caller.root)):
                with self.subTest(guard=guard, root=root):
                    result = self.run_guard_cli(
                        source, script, environment, caller.root, (root,)
                    )
                    self.assert_result(result, expected, 0)

    def test_relative_github_event_path_uses_the_selected_repository(self):
        repo = self.cli_repository()
        base = repo.head()
        repo.write('change.py', 'print("example")\n')
        repo.commit()
        repo.write(
            'event.json',
            json.dumps(
                {
                    'pull_request': {
                        'body': f'Decision: {DECISION}',
                        'labels': [],
                        'base': {'sha': base},
                        'head': {'sha': repo.head()},
                    }
                }
            ),
        )
        caller = self.repo()
        caller.write('event.json', '{}')
        source = self.cli_repository()
        source.write('event.json', '{}')
        environment = {'GITHUB_EVENT_PATH': 'event.json'}
        for guard in ('pr', 'design_link'):
            script = f'raicho_check_{guard}.py'
            expected = self.run_guard(repo, script, environment)
            for location, arguments in ((repo, ()), (source, (str(repo.root),))):
                with self.subTest(guard=guard, arguments=arguments):
                    result = self.run_guard_cli(
                        location, script, environment, caller.root, arguments
                    )
                    self.assert_result(result, expected, 0)

    def test_extra_root_arguments_are_rejected(self):
        repo = self.cli_repository()
        for guard in GUARDS:
            with self.subTest(guard=guard):
                result = self.run_guard_cli(
                    repo,
                    f'raicho_check_{guard}.py',
                    {},
                    repo.root,
                    (str(repo.root), str(repo.root)),
                )
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, '')
                self.assertIn('FAIL:', result.stderr)
                self.assertIn('repository root', result.stderr)
