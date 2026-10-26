from automation.repository.check_source_naming import shell_header
from automation.testing.guard_fixtures import GuardTestCase


class ShellShebangTests(GuardTestCase):
    def test_recognizes_shells_after_supported_env_options(self):
        headers = [
            '#!/bin/sh',
            '#!/bin/bash -e',
            '#!/usr/bin/env bash',
            '#!/usr/bin/env -S -i bash',
            '#!/usr/bin/env -S --ignore-environment sh',
            '#!/usr/bin/env --split-string -i bash',
            '#!/usr/bin/env --split-string=-i bash -e',
            '#!/usr/bin/env -Sbash -e',
            '#!/usr/bin/env -vS bash',
            '#!/usr/bin/env -ivS bash',
            '#!/usr/bin/env -vSbash -e',
            '#!/usr/bin/env -S -vi bash',
            '#!/usr/bin/env -S -vu HOME bash',
            '#!/usr/bin/env -S -viC/tmp bash',
            '#!/usr/bin/env -S -va script bash',
            '#!/usr/bin/env -S -vaiv bash',
            '#!/usr/bin/env -S -v -u HOME -C /tmp -a script bash',
            '#!/usr/bin/env -S --debug --unset=HOME --chdir=/tmp sh',
            '#!/usr/bin/env -S --argv0=script /bin/bash',
            '#!/usr/bin/env -S -uHOME -C/tmp -ascript bash',
            '#!/usr/bin/env -S -- MODE=test /bin/bash -e',
            '#!/usr/bin/env -S MODE=test EMPTY= bash',
            '#!/usr/bin/env -S - MODE=test sh',
        ]
        for header in headers:
            with self.subTest(header=header):
                self.assertTrue(shell_header(header.encode()))

    def test_option_values_and_arguments_are_not_interpreters(self):
        headers = [
            '#!/usr/bin/env -S -u bash python3',
            '#!/usr/bin/env -S --unset=bash python3',
            '#!/usr/bin/env -S --chdir bash python3',
            '#!/usr/bin/env -S --argv0 bash python3',
            '#!/usr/bin/env -S MODE=bash python3',
            '#!/usr/bin/env -S python3 bash',
            '#!/usr/bin/env -S MODE=test -- bash',
            '#!/usr/bin/env -S -- -i bash',
            '#!/usr/bin/env -S ${INTERPRETER}',
            '#!/usr/bin/env -vS -vu bash python3',
            '#!/usr/bin/env -vS -viubash python3',
            '#!/usr/bin/env -vS -vC bash python3',
            '#!/usr/bin/env -vS -vabash python3',
            '#!/usr/bin/env -vS python3 bash',
            '#!/usr/bin/env -S -- -vS bash',
            '#!/usr/bin/env -S MODE=test -vS bash',
        ]
        for header in headers:
            with self.subTest(header=header):
                self.assertFalse(shell_header(header.encode()))

    def test_malformed_or_unsupported_headers_are_not_shells(self):
        headers = [
            b'ordinary text bash',
            b'#!',
            b'#!/usr/bin/env',
            b'#!/usr/bin/env -S',
            b'#!/usr/bin/env -S -u',
            b'#!/usr/bin/env -S --chdir',
            b'#!/usr/bin/env -S --argv0',
            b'#!/usr/bin/env -S --unknown bash',
            b'#!/usr/bin/env -S --unset=HOME',
            b'#!/usr/bin/env -S "bash',
            b'#!/usr/bin/env -S \xff bash',
            b'#!/usr/bin/env -vS',
            b'#!/usr/bin/env -S -vu',
            b'#!/usr/bin/env -S -vx bash',
            b'#!/usr/bin/env -vxS bash',
        ]
        for header in headers:
            with self.subTest(header=header):
                self.assertFalse(shell_header(header))

    def test_env_options_cannot_bypass_source_filename_guard(self):
        repo = self.repo()
        header = '#!/usr/bin/env -S -i bash\ntouch should_not_exist\n'
        repo.write('bad-name', header)
        repo.write('valid_name', header)
        repo.write('python-file', '#!/usr/bin/env -S -u bash python3\n')
        result = self.run_guard(repo, 'check_source_naming.py', {})
        self.assertEqual(result.returncode, 1)
        self.assertIn('FAIL: bad-name must use lowercase snake_case', result.stderr)
        self.assertNotIn('valid_name', result.stderr)
        self.assertNotIn('python-file', result.stderr)
        self.assertFalse((repo.root / 'should_not_exist').exists())

    def test_bundled_env_options_cannot_bypass_source_filename_guard(self):
        for options in ('-vS bash', '-ivS bash', '-vSbash'):
            with self.subTest(options=options):
                repo = self.repo()
                header = f'#!/usr/bin/env {options}\ntouch should_not_exist\n'
                repo.write('bad-name', header)
                repo.write('valid_name', header)
                repo.write('python-file', '#!/usr/bin/env -vS -vu bash python3\n')
                result = self.run_guard(repo, 'check_source_naming.py', {})
                self.assertEqual(result.returncode, 1)
                self.assertIn(
                    'FAIL: bad-name must use lowercase snake_case', result.stderr
                )
                self.assertNotIn('valid_name', result.stderr)
                self.assertNotIn('python-file', result.stderr)
                self.assertFalse((repo.root / 'should_not_exist').exists())
