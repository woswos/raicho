import json
import tempfile
import unittest
from pathlib import Path

from mailprobe.tests.proxy.fault_state import FaultState, write_json


class FaultStateTests(unittest.TestCase):
    def test_default_normal_and_metadata_counter_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            state = FaultState(Path(directory))
            self.assertEqual(state.setting('smtp'), 'normal')
            state.record('smtp_accepted')
            state.record('smtp_accepted')
            restored = FaultState(Path(directory))
            self.assertEqual(restored.events, {'smtp_accepted': 2})

    def test_invalid_settings_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            state = FaultState(Path(directory))
            write_json(state.settings_path, {'smtp': 'unexpected', 'imap': 'normal'})
            with self.assertRaises(ValueError):
                state.setting('smtp')
            state.settings_path.write_text('{broken')
            with self.assertRaises(json.JSONDecodeError):
                state.setting('smtp')


if __name__ == '__main__':
    unittest.main()
