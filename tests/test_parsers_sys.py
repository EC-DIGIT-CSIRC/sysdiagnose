import os
import unittest

from sysdiagnose.parsers.sys import SystemVersionParser
from tests import SysdiagnoseTestCase


class TestParsersSys(SysdiagnoseTestCase):
    productinfo_keys = ["ProductName", "ProductBuildVersion", "ProductVersion", "BuildID", "SystemImageID"]
    productnames = ["iPhone OS", "Watch OS", "Apple TVOS"]

    def test_get_product_info(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id):
                p = SystemVersionParser(self.sd.config, case_id=case_id)
                files = p.get_log_files()
                if not files:
                    self.skipTest("No SystemVersion.plist file present")

                p.save_result(force=True)
                self.assertTrue(os.path.isfile(p.output_file))

                result = p.get_result()
                self.assertGreater(len(result), 0)
                for item in result:
                    self.assertTrue(
                        item["data"].keys() | self.productinfo_keys == item["data"].keys()
                    )  # check if the result contains at least the following keys
                    self.assertTrue(
                        item["data"]["ProductName"] in self.productnames
                    )  # check if the result contains at least the following keys
                    self.assertTrue(item["data"]["BuildID"])
                    self.assert_has_required_fields_jsonl(item)
                self.assert_result_summary_consistent(p, result)


if __name__ == "__main__":
    unittest.main()
