import unittest

from automation.build.application import test_summary


class ApplicationTests(unittest.TestCase):
    def test_summarizes_every_passing_test_binary(self):
        output = (
            'running 2 tests\n..\n'
            'test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured\n\n'
            'running 0 tests\n\n'
            'test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured\n'
            'test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured\n'
        )
        self.assertEqual(
            test_summary(output), 'Rust: 7 tests passed in 3 test binaries'
        )


if __name__ == '__main__':
    unittest.main()
