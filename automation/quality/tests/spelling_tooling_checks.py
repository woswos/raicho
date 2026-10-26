import tempfile
import unittest
from pathlib import Path
from unittest import mock

from automation.quality import spelling
from automation.quality.tests.quality_fixture import QualityFixture

# Split so the repository's own spelling check passes this file.
MISSPELLED = 'Te' + 'h'


class SpellingToolingChecks(QualityFixture):
    def test_typos_fail_the_check_until_fixed(self):
        source = self.write('docs/notes.md', f'{MISSPELLED} check runs.\n')
        self.check('lint-spelling', successful=False, diagnostic=f'notes.md:1:1: error: `{MISSPELLED}` should be `The`')
        self.check('format-spelling')
        self.assertEqual(source.read_text(), 'The check runs.\n')
        self.check('lint-spelling')

    def test_configured_identifiers_pass(self):
        self.write('open.rs', 'const FLAGS: u32 = WRONLY;\n')
        self.check('lint-spelling')

    def test_configuration_must_be_a_regular_file(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            mock.patch.object(spelling, 'REPOSITORY_ROOT', Path(directory)),
            self.assertRaisesRegex(ValueError, 'typos configuration is missing'),
        ):
            spelling.spelling(Path(directory), [], 'lint')


if __name__ == '__main__':
    unittest.main()
