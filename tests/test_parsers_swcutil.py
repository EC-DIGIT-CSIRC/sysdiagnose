from parsers.swcutil import parseswcutil
from tests import SysdiagnoseTestCase
import unittest


class TestParsersSwcutil(SysdiagnoseTestCase):

    log_path = "tests/testdata/iOS15/sysdiagnose_2023.05.24_13-29-15-0700_iPhone-OS_iPhone_19H349/swcutil_show.txt"

    db_keys = ['Service', 'App ID', 'App Version', 'App PI', 'Domain', 'Patterns', 'User Approval', 'Site/Fmwk Approval', 'Flags']

    def test_parseswcutil(self):
        result = parseswcutil(self.log_path)
        self.assertGreater(len(result), 0)
        self.assertTrue('headers' in result)
        self.assertTrue('network' in result)
        self.assertTrue('headers' in result)

        self.assertGreater(len(result['memory']), 0)
        self.assertGreater(len(result['db']), 0)
        self.assertEqual(list(result['db'][0].keys()), self.db_keys)


if __name__ == '__main__':
    unittest.main()
