import json
import unittest

from automation.build.rust_coverage import instrumented_executables


class RustCoverageTests(unittest.TestCase):
    def test_lists_each_built_executable_once(self):
        messages = [
            {
                'reason': 'compiler-artifact',
                'executable': '/target/debug/deps/server-1',
            },
            {'reason': 'compiler-artifact', 'executable': None},
            {'reason': 'build-script-executed', 'executable': '/target/build'},
            {
                'reason': 'compiler-artifact',
                'executable': '/target/debug/deps/server-1',
            },
            {
                'reason': 'compiler-artifact',
                'executable': '/target/debug/raicho-server',
            },
        ]
        self.assertEqual(
            instrumented_executables('\n'.join(map(json.dumps, messages))),
            ['/target/debug/deps/server-1', '/target/debug/raicho-server'],
        )


if __name__ == '__main__':
    unittest.main()
