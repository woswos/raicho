import unittest

from automation.build.python_tests import summary


class PythonTestsSummaryTests(unittest.TestCase):
    def test_counts_passed_tests_and_names_the_suite_directory(self):
        self.assertEqual(summary('.', 263, 0), 'Python: 263 tests passed')
        self.assertEqual(
            summary('automation/quality/tests', 27, 2),
            'Python: 25 tests passed, 2 skipped in automation/quality/tests',
        )


if __name__ == '__main__':
    unittest.main()
