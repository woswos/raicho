import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from raicho_inspect_connector_xpi import inspect_archive


class ProductionArchiveTests(unittest.TestCase):
    def archive(self, directory, contents=b'export {};', permissions=None):
        path = directory / 'connector.xpi'
        manifest = {
            'manifest_version': 2,
            'version': '0.2.0',
            'browser_specific_settings': {'gecko': {'id': 'connector@raicho'}},
            'permissions': ['storage'] if permissions is None else permissions,
        }
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('manifest.json', json.dumps(manifest))
            archive.writestr('extension/src/connector_transport.js', contents)
        return path

    def test_inspects_the_packaged_archive_for_secrets_and_probe_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            inspect_archive(self.archive(directory), b'private-token')
            for contents in (b'private-token', b'lifecycle_probe', b'mail_probe'):
                with self.assertRaises(AssertionError):
                    inspect_archive(self.archive(directory, contents), b'private-token')

    def test_rejects_mail_permissions_in_the_production_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.archive(
                Path(temporary), permissions=['storage', 'messagesRead']
            )
            with self.assertRaises(AssertionError):
                inspect_archive(path, b'private-token')
