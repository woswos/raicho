from automation.repository.check_skills import check_skills
from automation.testing.guard_fixtures import GuardTestCase


class SkillNamingTests(GuardTestCase):
    def skill(self, repo, name, metadata=''):
        repo.write(
            f'.agents/skills/{name}/SKILL.md',
            f'---\nname: {name}\ndescription: Example skill.\n{metadata}---\n# Example\n',
        )

    def test_kebab_case_workflow_name_is_valid(self):
        repo = self.repo()
        self.skill(repo, 'write-plan-doc')
        self.assertEqual(check_skills(repo.root), [])

    def test_skill_names_reject_underscores_uppercase_and_stray_hyphens(self):
        repo = self.repo()
        for name in ('bad_skill', 'BadSkill', '-bad', 'bad-', 'bad--skill'):
            self.skill(repo, name)
        failures = check_skills(repo.root)
        self.assertEqual(len(failures), 5)
        self.assertTrue(
            all('invalid skill directory name' in failure for failure in failures)
        )

    def test_scaffolding_name_requires_examples(self):
        repo = self.repo()
        self.skill(repo, 'add-endpoint')
        self.assertIn(
            'add-endpoint: add-* skills need one to three examples',
            check_skills(repo.root),
        )

    def test_scaffolding_examples_must_be_existing_files(self):
        repo = self.repo()
        repo.write(
            '.agents/skills/add-endpoint/SKILL.md',
            '---\nname: add-endpoint\ndescription: Example.\nexamples:\n'
            '  - server/endpoint.py\n---\nSee `server/endpoint.py`.\n',
        )
        self.assertTrue(
            any(
                'not an existing repository file' in failure
                for failure in check_skills(repo.root)
            )
        )
        repo.write('server/endpoint.py', '')
        self.assertEqual(check_skills(repo.root), [])
