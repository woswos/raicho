import json
import tempfile
from pathlib import Path


class PolicyFixture:
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.runtime = self.root / 'runtime'
        self.extension = self.root / 'extension'
        self.extension.mkdir()
        self.manifest = self.extension / 'manifest.json'
        self.manifest.write_text(
            json.dumps(
                {
                    'version': '0.1.0',
                    'browser_specific_settings': {'gecko': {'id': 'connector@raicho'}},
                }
            )
        )
        (self.extension / 'raicho-0.1.0.xpi').touch()
        self.token_file = self.root / 'token'
        self.token = 'ab' * 32
        self.token_file.write_text(self.token + '\n')
        self.environment = {
            'RAICHO_CONNECTOR_ENDPOINT': 'ws://listener:8081/connector/v1',
            'RAICHO_CONNECTOR_TOKEN_FILE': str(self.token_file),
        }
