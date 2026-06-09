import os
import unittest

from sysdiagnose.parsers.psthread import PsThreadParser
from tests import SysdiagnoseTestCase


class TestParsersPsthread(SysdiagnoseTestCase):
    def test_parse_psthread(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                p = PsThreadParser(self.sd.config, case_id=case_id)
                files = p.get_log_files()
                if not files:
                    self.fail(
                        f"No log files found for {case_id}: parser {p.module_name}, iOS {_case.get('ios_version')}"
                    )
                    self.skipTest("No ps_thread.txt file present")

                p.save_result(force=True)
                self.assertTrue(os.path.isfile(p.output_file))

                result = p.get_result()
                if result:  # not all logs contain data
                    for item in result:
                        self.assertTrue("command" in item["data"])
                        self.assertTrue("pid" in item["data"])
                        self.assertTrue("user" in item["data"])
                        self.assert_has_required_fields_jsonl(item)
                self.assert_result_summary_consistent(p, result)


if __name__ == "__main__":
    unittest.main()
