import os
import unittest

from sysdiagnose.parsers.remotectl_dumpstate import RemotectlDumpstateParser
from tests import SysdiagnoseTestCase


class TestParsersRemotectlDumpstate(SysdiagnoseTestCase):
    def test_get_remotectldumpstate(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get('ios_version')):
                p = RemotectlDumpstateParser(self.sd.config, case_id=case_id)

                files = p.get_log_files()
                if not files:
                    self.fail(
                        f"No log files found for {case_id}: parser {p.module_name}, iOS {_case.get('ios_version')}"
                    )
                    self.skipTest("No remotectl_dumpstate.txt file present")

                p.save_result(force=True)
                self.assertTrue(os.path.isfile(p.output_file))

                result = p.get_result()
                if result:
                    self.assertTrue("Local device" in result)
                self.assert_result_summary_consistent(p, result)


if __name__ == "__main__":
    unittest.main()
