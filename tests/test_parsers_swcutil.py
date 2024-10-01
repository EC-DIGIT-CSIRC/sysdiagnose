from sysdiagnose.parsers.swcutil import SwcutilParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersSwcutil(SysdiagnoseTestCase):
    def test_parseswcutil(self):
        for case_id, case in self.sd.cases().items():
            p = SwcutilParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            self.assertGreater(len(result), 0)
            self.assertTrue('headers' in result)
            self.assertTrue('network' in result)
            self.assertTrue('headers' in result)

            self.assertGreater(len(result['memory']), 0)
            self.assertGreater(len(result['db']), 0)


if __name__ == '__main__':
    unittest.main()
