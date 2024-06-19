from parsers.sys import parse_path, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersSys(SysdiagnoseTestCase):
    productinfo_keys = ['ProductName', 'ProductBuildVersion', 'ProductVersion', 'BuildID', 'SystemImageID']

    def test_getProductInfo(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            self.assertTrue(len(files) > 0)
            print(f'Parsing {files}')
            result = parse_path(log_root_path)
            self.assertGreater(len(result), 0)

            self.assertTrue(result.keys() | self.productinfo_keys == result.keys())  # check if the result contains at least the following keys
            self.assertTrue('iPhone OS' in result['ProductName'])
            self.assertTrue(result['BuildID'])


if __name__ == '__main__':
    unittest.main()
