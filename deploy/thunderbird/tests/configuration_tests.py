import json
import os
import tempfile
import unittest
from pathlib import Path

from automation.paths import REPOSITORY_ROOT
from deploy.thunderbird.policy import read_token, validate_endpoint

RULES = json.loads((REPOSITORY_ROOT / 'protocol/fixtures/configuration/connector.json').read_text())


class ConnectorConfigurationTests(unittest.TestCase):
    def read(self, token):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'connector.token'
            path.write_text(token)
            os.chmod(path, 0o600)
            return read_token(path)

    def test_tokens_follow_the_shared_rules(self):
        for token in RULES['tokens']['valid']:
            with self.subTest(token=token):
                self.assertEqual(self.read(token), token)
        for token in RULES['tokens']['invalid']:
            with self.subTest(token=token):
                with self.assertRaises(ValueError):
                    self.read(token)

    def test_endpoints_follow_the_shared_rules(self):
        for endpoint in RULES['endpoints']['valid']:
            with self.subTest(endpoint=endpoint):
                validate_endpoint(endpoint)
        for endpoint in RULES['endpoints']['invalid']:
            with self.subTest(endpoint=endpoint):
                with self.assertRaises(ValueError):
                    validate_endpoint(endpoint)


if __name__ == '__main__':
    unittest.main()
