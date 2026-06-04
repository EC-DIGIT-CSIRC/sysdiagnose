import os
import unittest

from sysdiagnose.parsers.containermanager import ContainerManagerParser
from tests import SysdiagnoseTestCase


class TestParsersContainermanager(SysdiagnoseTestCase):
    def test_parsecontainermanager(self):
        for case_id, _case in self.sd.cases().items():
            p = ContainerManagerParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            if len(files) == 0:
                self.skipTest(f"No log files found for {case_id}")

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            for item in result:
                self.assertTrue("hexID" in item["data"])
                self.assertTrue("loglevel" in item["data"])
                self.assert_has_required_fields_jsonl(item)
            self.assert_result_summary_consistent(p, result)


if __name__ == "__main__":
    unittest.main()
