from parsers.sys import getProductInfo
from tests import SysdiagnoseTestCase
import unittest


class TestParsersSys(SysdiagnoseTestCase):

    log_path = "tests/testdata/iOS15/sysdiagnose_2023.05.24_13-29-15-0700_iPhone-OS_iPhone_19H349/logs/SystemVersion/SystemVersion.plist"

    productinfo_keys = ['ProductName', 'ProductBuildVersion', 'ProductVersion', 'BuildID', 'SystemImageID']

    def test_getProductInfo(self):
        result = getProductInfo(self.log_path)
        self.assertGreater(len(result), 0)

        self.assertTrue(result.keys() | self.productinfo_keys == result.keys())  # check if the result contains at least the following keys
        self.assertTrue('iPhone OS' in result['ProductName'])
        self.assertTrue(result['BuildID'])


if __name__ == '__main__':
    unittest.main()
