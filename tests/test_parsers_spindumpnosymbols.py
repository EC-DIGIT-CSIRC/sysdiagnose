import unittest

from parsers.spindumpnosymbols import parsespindumpNS

class TestParsersSpindumpnosymbols(unittest.TestCase):

    log_path = "tests/testdata/iOS15/sysdiagnose_2023.05.24_13-29-15-0700_iPhone-OS_iPhone_19H349/spindump-nosymbols.txt"


    def test_parsespindumpNS(self):
        result = parsespindumpNS(self.log_path)
        self.assertGreater(len(result), 0)
        self.assertTrue('iPhone OS' in result['OS Version'])
        self.assertTrue('rootdev' in result['Boot args'])
        self.assertGreater(len(result['processes']), 0)


if __name__ == '__main__':
    unittest.main()
