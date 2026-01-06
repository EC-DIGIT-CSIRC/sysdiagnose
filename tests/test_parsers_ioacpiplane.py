from sysdiagnose.parsers.ioacpiplane import IOACPIPlaneParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersIOACPIPlane(SysdiagnoseTestCase):

    def test_parse_case(self):
        for case_id, case in self.sd.cases().items():
            p = IOACPIPlaneParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))


if __name__ == '__main__':
    unittest.main()
