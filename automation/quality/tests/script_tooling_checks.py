import unittest

from automation.quality.tests.quality_fixture import QualityFixture

UNFORMATTED_BASH = '#!/usr/bin/env bash\nif true; then\n  echo ready\nfi\n'
FORMATTED_BASH = '#!/usr/bin/env bash\nif true; then\n    echo ready\nfi\n'
UNFORMATTED_PYTHON = 'answer = [1,\n  2]\n'


class ScriptToolingChecks(QualityFixture):
    def test_bash_format_check_reports_and_format_rewrites(self):
        path = self.write('tool.bash', UNFORMATTED_BASH)
        self.check('format-check-bash', successful=False, diagnostic='tool.bash')
        self.assertEqual(path.read_text(), UNFORMATTED_BASH)
        self.check('format-bash', diagnostic='tool.bash')
        self.assertEqual(path.read_text(), FORMATTED_BASH)
        self.check('format-check-bash')
        self.check('lint-bash')

    def test_bash_lint_rejects_syntax_errors_and_shellcheck_findings(self):
        path = self.write('tool.bash', '#!/usr/bin/env bash\nif true; then\n')
        self.check('lint-bash', successful=False, diagnostic='tool.bash')
        path.write_text('#!/usr/bin/env bash\necho $1\n')
        self.check('lint-bash', successful=False, diagnostic='SC2086')

    def test_bash_lint_requires_braces_but_allows_the_excluded_checks(self):
        path = self.write('tool.bash', '#!/usr/bin/env bash\necho "$HOME"\n')
        self.check('lint-bash', successful=False, diagnostic='SC2250')
        path.write_text('#!/usr/bin/env bash\nif [ ! -z "${1}" ]; then\n    echo "${1}"\nfi\n')
        self.check('lint-bash')

    def test_python_format_check_reports_and_format_rewrites(self):
        path = self.write('example.py', UNFORMATTED_PYTHON)
        self.check('format-check-python', successful=False, diagnostic='example.py')
        self.assertEqual(path.read_text(), UNFORMATTED_PYTHON)
        self.check('format-python')
        self.assertEqual(path.read_text(), 'answer = [1, 2]\n')
        self.check('format-check-python')

    def test_python_lint_rejects_unused_imports(self):
        self.write('example.py', 'import os\n')
        self.check('lint-python', successful=False, diagnostic='F401')


if __name__ == '__main__':
    unittest.main()
