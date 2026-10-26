import re
import unittest

from automation.paths import REPOSITORY_ROOT
from automation.quality.runner import TARGETS


def make_list(makefile, name):
    return re.search(rf'^{name} := (.*)$', makefile, re.MULTILINE)[1].split()


class QualityTargetTests(unittest.TestCase):
    def setUp(self):
        self.makefile = (REPOSITORY_ROOT / 'Makefile').read_text().replace('\\\n', ' ')

    def test_make_offers_exactly_the_runner_targets(self):
        self.assertEqual(
            sorted(make_list(self.makefile, 'QUALITY_TARGETS')), sorted(TARGETS)
        )

    def test_every_language_formats_and_checks_alone(self):
        for language in ('bash', 'python', 'javascript', 'rust', 'sql'):
            with self.subTest(language=language):
                self.assertIn(f'format-{language}', TARGETS)
                self.assertIn(f'format-check-{language}', TARGETS)

    def test_rewriting_targets_use_the_writable_service(self):
        writing = make_list(self.makefile, 'WRITING_TARGETS')
        for target in TARGETS:
            if target.startswith('format') and not target.startswith('format-check'):
                with self.subTest(target=target):
                    self.assertIn(target, writing)


if __name__ == '__main__':
    unittest.main()
