import json
import os
import unittest

from deploy.thunderbird.policy import write_policies
from deploy.thunderbird.tests.policy_fixture import PolicyFixture


class PolicyValidationTests(PolicyFixture, unittest.TestCase):
    def test_partial_configuration_fails_without_exposing_values(self):
        for missing in self.environment:
            environment = self.environment.copy()
            del environment[missing]
            with self.subTest(missing=missing):
                with self.assertRaisesRegex(ValueError, 'configured together') as context:
                    write_policies(self.runtime, self.extension, environment)
                self.assertNotIn(self.token, str(context.exception))

    def test_missing_token_is_reported_without_path(self):
        self.token_file.unlink()
        with self.assertRaisesRegex(ValueError, 'could not be read') as context:
            write_policies(self.runtime, self.extension, self.environment)
        self.assertNotIn(str(self.token_file), str(context.exception))

    def test_nonregular_secret_fails_without_blocking(self):
        self.token_file.unlink()
        os.mkfifo(self.token_file)
        with self.assertRaisesRegex(ValueError, 'regular file'):
            write_policies(self.runtime, self.extension, self.environment)

    def test_bad_manifest_or_absent_archive_fails(self):
        for manifest in ('not json', '[]', '{}', '{"version":"../escape"}'):
            with self.subTest(manifest=manifest):
                self.manifest.write_text(manifest)
                with self.assertRaisesRegex(ValueError, 'Packaged extension'):
                    write_policies(self.runtime, self.extension, {})
        self.manifest.write_text(json.dumps({'version': '0.1.0'}))
        with self.assertRaisesRegex(ValueError, 'Packaged extension'):
            write_policies(self.runtime, self.extension, {})

    def test_missing_archive_fails(self):
        (self.extension / 'raicho-0.1.0.xpi').unlink()
        with self.assertRaisesRegex(ValueError, 'archive is missing'):
            write_policies(self.runtime, self.extension, {})


if __name__ == '__main__':
    unittest.main()
