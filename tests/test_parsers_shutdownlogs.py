import unittest

from parsers.shutdownlogs import parse_shutdownlog

class TestParsersShutdownlogs(unittest.TestCase):

    log_path = "tests/testdata/iOS15/sysdiagnose_2023.05.24_13-29-15-0700_iPhone-OS_iPhone_19H349/system_logs.logarchive/Extra/shutdown.log"


    def test_parse_shutdownlog(self):
        result = parse_shutdownlog(self.log_path)
        self.assertGreater(len(result['data']), 0)


if __name__ == '__main__':
    unittest.main()