import os
import unittest

from sysdiagnose.parsers.ioservice import IOServiceParser
from tests import SysdiagnoseTestCase


class TestParsersIOService(SysdiagnoseTestCase):

    def test_parse_case(self):
        for case_id, _case in self.sd.cases().items():
            p = IOServiceParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))


if __name__ == '__main__':
    unittest.main()
