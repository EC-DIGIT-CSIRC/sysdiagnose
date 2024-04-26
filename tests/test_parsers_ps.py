import unittest

from parsers.ps import parse_ps

class TestParsersPs(unittest.TestCase):

    log_path = "tests/testdata/iOS15/sysdiagnose_2023.05.24_13-29-15-0700_iPhone-OS_iPhone_19H349/ps.txt"


    def test_parse_ps(self):
        result = parse_ps(self.log_path)
        self.assertGreater(len(result), 0)
        self.assertEqual(result[1]["COMMAND"], '/sbin/launchd')


if __name__ == '__main__':
    unittest.main()