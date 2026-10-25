import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from automation.paths import REPOSITORY_ROOT
from extension.tests.build_runner import run_builder


class ProbePackagingTests(unittest.TestCase):
    def test_probe_is_a_separate_explicitly_selected_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'probe.xpi'
            result = run_builder(
                '--output',
                str(output),
                '--source-root',
                str(REPOSITORY_ROOT / 'extension/mailprobe'),
                cwd=directory,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                manifest = json.loads(archive.read('manifest.json'))
        self.assertNotIn('messages.send', manifest['permissions'])
        self.assertEqual(manifest['optional_permissions'], ['messages.send'])
        self.assertIn('mailprobe/src/dispatcher.js', names)
        self.assertIn('permission.html', names)
        self.assertFalse(any(name.startswith('protocol/') for name in names))
