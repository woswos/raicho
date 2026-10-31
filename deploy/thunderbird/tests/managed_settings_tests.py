import json
import os
import tempfile
import unittest
from pathlib import Path

from automation.paths import REPOSITORY_ROOT
from deploy.thunderbird.managed_settings import read_token, validate_endpoint

RULES = json.loads((REPOSITORY_ROOT / 'protocol/fixtures/configuration/connector.json').read_text())
EXTRA_INVALID_ENDPOINTS = ('ws://listener:invalid/connector/v1', 'ws://listener/\x7fconnector/v1')
EXTRA_INVALID_TOKENS = ('ab' * 32 + '\n\n', '秘密', 'a' * 10000)


class ManagedSettingsTests(unittest.TestCase):
    def read(self, token):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'connector.token'
            path.write_text(token)
            os.chmod(path, 0o600)
            return read_token(path)

    def test_tokens_follow_the_shared_rules_without_exposing_rejections(self):
        for token in RULES['tokens']['valid']:
            with self.subTest(token=token):
                self.assertEqual(self.read(token), token)
        for token in (*RULES['tokens']['invalid'], *EXTRA_INVALID_TOKENS):
            with self.subTest(length=len(token)):
                with self.assertRaisesRegex(ValueError, 'Connector token') as context:
                    self.read(token)
                if token.strip():
                    self.assertNotIn(token.strip(), str(context.exception))

    def test_endpoints_follow_the_shared_rules_without_exposing_rejections(self):
        for endpoint in RULES['endpoints']['valid']:
            with self.subTest(endpoint=endpoint):
                validate_endpoint(endpoint)
        for endpoint in (*RULES['endpoints']['invalid'], *EXTRA_INVALID_ENDPOINTS):
            with self.subTest(endpoint=endpoint):
                with self.assertRaisesRegex(ValueError, 'Connector endpoint') as context:
                    validate_endpoint(endpoint)
                if endpoint.strip():
                    self.assertNotIn(endpoint.strip(), str(context.exception))
                self.assertNotIn('secret', str(context.exception))


if __name__ == '__main__':
    unittest.main()
