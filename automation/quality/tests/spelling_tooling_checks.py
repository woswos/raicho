import unittest

from automation.quality.tests.project_fixture import ProjectFixture

# Split so the repository's own spelling check passes this file.
MISSPELLED = 'Te' + 'h'


class SpellingToolingChecks(ProjectFixture):
    def test_typos_fail_the_check_until_fixed(self):
        source = self.write('docs/notes.md', f'{MISSPELLED} check runs.\n')
        self.check('lint-spelling', successful=False, diagnostic=f'notes.md:1:1: error: `{MISSPELLED}` should be `The`')
        self.check('lint-spelling', successful=False, diagnostic='FAIL: typos exited with status 2')
        self.check('format-spelling')
        self.assertEqual(source.read_text(), 'The check runs.\n')
        self.check('lint-spelling')

    def test_configured_identifiers_pass(self):
        self.write('open.rs', 'const FLAGS: u32 = WRONLY;\n')
        self.check('lint-spelling')


if __name__ == '__main__':
    unittest.main()
