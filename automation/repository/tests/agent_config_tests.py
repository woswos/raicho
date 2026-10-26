from automation.paths import REPOSITORY_ROOT
from automation.repository.check_agent_config import (
    REQUIRED_IMPORTS,
    check_agent_config,
)
from automation.repository.check_skills import check_skills
from automation.testing.guard_fixtures import GuardTestCase


class AgentConfigTests(GuardTestCase):
    def test_live_repository_matches_the_loader_contract(self):
        imported = [
            line[1:]
            for line in (REPOSITORY_ROOT / 'AGENTS.md').read_text().splitlines()
            if line.startswith('@')
        ]
        self.assertEqual(imported, list(REQUIRED_IMPORTS))
        self.assertEqual(check_agent_config(REPOSITORY_ROOT), [])
        self.assertEqual(check_skills(REPOSITORY_ROOT), [])

    def test_instruction_fixture_passes(self):
        self.assertEqual(check_agent_config(self.instructions().root), [])

    def test_always_loaded_import_is_required(self):
        repo = self.instructions()
        text = (repo.root / 'AGENTS.md').read_text()
        text = text.replace('@docs/contributing/workflow.md\n', '')
        (repo.root / 'AGENTS.md').write_text(text)
        failures = check_agent_config(repo.root)
        self.assertIn(
            'AGENTS.md must reference docs/contributing/workflow.md', failures
        )

    def test_mistyped_citation_fails(self):
        repo = self.instructions()
        text = (
            (repo.root / 'AGENTS.md')
            .read_text()
            .replace(
                'docs/contributing/git-and-pull-requests.md',
                'docs/contributing/git-and-pull-request.md',
            )
        )
        (repo.root / 'AGENTS.md').write_text(text)
        failures = check_agent_config(repo.root)
        self.assertIn(
            'missing instruction file: docs/contributing/git-and-pull-request.md',
            failures,
        )

    def test_cited_path_cannot_escape(self):
        repo = self.instructions()
        with (repo.root / 'AGENTS.md').open('a') as handle:
            handle.write('- Outside: `../outside.md`\n')
        failures = check_agent_config(repo.root)
        self.assertIn(
            'instruction reference escapes repository: ../outside.md', failures
        )

    def test_malformed_skill_fails(self):
        repo = self.repo()
        repo.write('.agents/skills/example/SKILL.md', 'hello\n')
        self.assertIn(
            'example: missing YAML frontmatter opening delimiter',
            check_skills(repo.root),
        )


if __name__ == '__main__':
    import unittest

    unittest.main()
