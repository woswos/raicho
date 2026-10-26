import tempfile
import unittest
from pathlib import Path

from automation.build.lcov import merge, summary
from automation.paths import REPOSITORY_ROOT


class LcovTests(unittest.TestCase):
    def test_a_line_covered_by_any_report_counts_as_covered(self):
        absolute = REPOSITORY_ROOT / 'protocol/typescript/src/channel.ts'
        with tempfile.TemporaryDirectory() as directory:
            protocol = Path(directory) / 'protocol.info'
            protocol.write_text(
                'SF:protocol/typescript/src/channel.ts\nDA:1,0\nDA:2,3\nend_of_record\n'
            )
            extension = Path(directory) / 'extension.info'
            extension.write_text(
                f'SF:{absolute}\nDA:1,1\nDA:3,0\nend_of_record\n'
                'SF:/tmp/outside.py\nDA:1,1\nend_of_record\n'
            )
            merged = merge([protocol, extension])
        self.assertEqual(merged[absolute], {1: 1, 2: 3, 3: 0})
        self.assertEqual(
            [row.split() for row in summary(merged)],
            [
                ['66.7%', '2/3', 'protocol/typescript/src/channel.ts'],
                ['66.7%', '2/3', 'total'],
            ],
        )


if __name__ == '__main__':
    unittest.main()
