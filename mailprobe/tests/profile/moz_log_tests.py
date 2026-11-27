import unittest

from mailprobe.tests.profile.moz_log import redacted


class MozLogTests(unittest.TestCase):
    def test_drops_authentication_lines(self):
        lines = ['1 capability', '2 login "sender" "fixture"', '3 authenticate PLAIN', '4 select "INBOX"']
        self.assertEqual(redacted(lines), ['1 capability', '4 select "INBOX"'])


if __name__ == '__main__':
    unittest.main()
