import os
import unittest

from sysdiagnose.parsers.iodevicetree import IODeviceTreeParser
from tests import SysdiagnoseTestCase


class TestParsersIODeviceTree(SysdiagnoseTestCase):
    def test_parse_case(self):
        for case_id, _case in self.sd.cases().items():
            p = IODeviceTreeParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            if not files:
                self.skipTest(f"No log files found for {case_id}")

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))
            self.assert_result_summary_consistent(p, p.get_result())


if __name__ == "__main__":
    unittest.main()
