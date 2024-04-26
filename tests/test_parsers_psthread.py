import unittest

from parsers.psthread import parse_ps_thread

class TestParsersPsthread(unittest.TestCase):

    log_path = "tests/testdata/sysdiagnose_2023.05.24_13-29-15-0700_iPhone-OS_iPhone_19H349/ps_thread.txt"


    def test_parse_psthread(self):
        result = parse_ps_thread(self.log_path)
        self.assertGreater(len(result), 0)
        self.assertEqual(result[0]["COMMAND"], '/sbin/launchd')


if __name__ == '__main__':
    unittest.main()