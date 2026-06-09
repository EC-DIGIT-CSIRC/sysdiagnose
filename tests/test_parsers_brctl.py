import os
import unittest

from sysdiagnose.parsers.brctl import BrctlParser
from tests import SysdiagnoseTestCase


class TestParsersBrctl(SysdiagnoseTestCase):
    def test_parsebrctl(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                p = BrctlParser(self.sd.config, case_id=case_id)
                folders = p.get_log_files()
                if not folders:
                    self.fail(
                        f"No log files found for {case_id}: parser {p.module_name}, iOS {_case.get('ios_version')}"
                    )
                    self.skipTest("No brctl folder found")

                p.save_result(force=True)
                self.assertTrue(os.path.isfile(p.output_file))

                print(f"Parsing {folders}")
                result = p.get_result()
                if result:
                    self.assertTrue("containers" in result)
                    self.assertTrue("boot_history" in result)
                    self.assertTrue("server_state" in result)
                    self.assertTrue("client_state" in result)
                    self.assertTrue("system" in result)
                    self.assertTrue("scheduler" in result)
                    self.assertTrue("applibrary" in result)
                    self.assertTrue("app_library_id" in result)
                    self.assertTrue("app_ids" in result)
                self.assert_result_summary_consistent(p, result)


if __name__ == "__main__":
    unittest.main()
