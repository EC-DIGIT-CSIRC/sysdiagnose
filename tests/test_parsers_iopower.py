import os
import unittest

from sysdiagnose.parsers.iopower import IOPowerParser
from tests import SysdiagnoseTestCase


class TestParsersIOPower(SysdiagnoseTestCase):

    def test_parse_case(self):
        for case_id, _case in self.sd.cases().items():
            p = IOPowerParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))


if __name__ == '__main__':
    unittest.main()
