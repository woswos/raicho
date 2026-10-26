import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from raicho_quality_sql import sql


class SqlConfigurationTests(unittest.TestCase):
    def test_missing_configuration_fails_even_without_sources(self):
        with tempfile.TemporaryDirectory(prefix='raicho-sql-config-') as directory:
            root = Path(directory)
            with (
                patch('raicho_quality_sql.require_tools'),
                self.assertRaisesRegex(ValueError, 'SQL configuration is missing'),
            ):
                sql(root, [], 'lint', root)

    def test_symlinked_configuration_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='raicho-sql-config-') as directory:
            root = Path(directory)
            configuration = root / 'configuration'
            configuration.write_text('[sqlfluff]\ndialect = sqlite\n')
            (root / '.sqlfluff').symlink_to(configuration)
            with (
                patch('raicho_quality_sql.require_tools'),
                self.assertRaisesRegex(ValueError, 'not a regular file'),
            ):
                sql(root, [], 'lint', root)
