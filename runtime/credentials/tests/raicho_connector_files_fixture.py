import os
import tempfile
import unittest
from pathlib import Path

from runtime.credentials import raicho_connector_files as connector_files


class ConnectorTokenFilesTestCase(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='raicho-connector-files-')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)

    def operate(self, operation):
        return connector_files.operate(
            operation, self.directory, os.getuid(), os.getgid()
        )

    def path(self, name):
        return self.directory / f'connector.{name}'

    def initialized(self):
        self.assertEqual(self.operate('init'), 'pending')
        self.operate('publish')
        self.operate('finish')
        return self.path('token').read_bytes()
