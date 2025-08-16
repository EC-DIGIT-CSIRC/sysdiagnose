from sysdiagnose.parsers.sys import SystemVersionParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersSys(SysdiagnoseTestCase):
    productinfo_keys = ['ProductName', 'ProductBuildVersion', 'ProductVersion', 'BuildID', 'SystemImageID']
    productnames = ['iPhone OS', 'Watch OS', 'Apple TVOS']

    def test_getProductInfo(self):
        for case_id, case in self.sd.cases().items():
            p = SystemVersionParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            self.assertGreater(len(result), 0)
            for item in result:
                self.assertTrue(item['data'].keys() | self.productinfo_keys == item['data'].keys())  # check if the result contains at least the following keys
                self.assertTrue(item['data']['ProductName'] in self.productnames)  # check if the result contains at least the following keys
                self.assertTrue(item['data']['BuildID'])
                self.assert_has_required_fields_jsonl(item)


if __name__ == '__main__':
    unittest.main()
