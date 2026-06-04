import os
import unittest

from sysdiagnose.parsers.ioacpiplane import IOACPIPlaneParser
from tests import SysdiagnoseTestCase


class TestParsersIOACPIPlane(SysdiagnoseTestCase):
    def test_parse_case(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id):
                p = IOACPIPlaneParser(self.sd.config, case_id=case_id)
                files = p.get_log_files()
                if not files:
                    self.skipTest("No IOACPIPlane file present")

                p.save_result(force=True)
                self.assertTrue(os.path.isfile(p.output_file))
                self.assert_result_summary_consistent(p, p.get_result())


if __name__ == "__main__":
    unittest.main()
