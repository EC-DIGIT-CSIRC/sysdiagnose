import os
import unittest

from sysdiagnose.parsers.shutdownlogs import ShutdownLogsParser
from tests import SysdiagnoseTestCase


class TestParsersShutdownlogs(SysdiagnoseTestCase):
    def test_parse_shutdownlog(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                p = ShutdownLogsParser(self.sd.config, case=_case)
                files = p.get_log_files()
                if not files:
                    self.fail(
                        f"No log files found for {case_id}: parser {p.module_name}, iOS {_case.get('ios_version')}"
                    )
                    self.skipTest("No shutdown.log file present")

                p.save_result(force=True)
                self.assertTrue(os.path.isfile(p.output_file))

                result = p.get_result()
                self.assertGreater(len(result), 0)
                for item in result:
                    self.assertTrue("pid" in item["data"])
                    self.assertTrue("path" in item["data"])
                    self.assert_has_required_fields_jsonl(item)
                self.assert_result_summary_consistent(p, result)


if __name__ == "__main__":
    unittest.main()
