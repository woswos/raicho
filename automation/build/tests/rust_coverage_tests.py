import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from automation.build import rust_coverage
from automation.build.rust_coverage import instrumented_executables

LISTING = '\n'.join(
    json.dumps({'reason': 'compiler-artifact', 'executable': executable})
    for executable in ('/target/deps/protocol-1', '/target/deps/server-2')
)


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

    def test_instruments_the_tests_then_exports_every_binary_as_lcov(self):
        def run(command, **_):
            outputs = {
                'cargo': LISTING,
                'rustc': '/sysroot/lib/rustlib/x86_64/lib\n',
                'llvm-cov': 'SF:server/src/http.rs\nend_of_record\n',
            }
            return subprocess.CompletedProcess(
                command, 0, stdout=outputs.get(Path(str(command[0])).name, '')
            )

        with (
            tempfile.TemporaryDirectory() as directory,
            mock.patch.object(rust_coverage, 'cargo_test') as cargo_test,
            mock.patch.object(rust_coverage, 'run', side_effect=run) as commands,
        ):
            output = Path(directory)
            rust_coverage.rust(output)
            report = (output / 'rust.info').read_text()
        environment = cargo_test.call_args.kwargs['env']
        self.assertEqual(environment['RUSTFLAGS'], '-C instrument-coverage')
        self.assertTrue(environment['LLVM_PROFILE_FILE'].endswith('%p-%m.profraw'))
        export = commands.call_args_list[-1].args[0]
        self.assertEqual(str(export[0]), '/sysroot/lib/rustlib/x86_64/bin/llvm-cov')
        self.assertIn('/target/deps/protocol-1', export)
        self.assertIn('-object=/target/deps/server-2', export)
        self.assertEqual(report, 'SF:server/src/http.rs\nend_of_record\n')


if __name__ == '__main__':
    unittest.main()
