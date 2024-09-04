from parsers.accessibility_tcc import AccessibilityTccParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersAccessibilityTcc(SysdiagnoseTestCase):

    def test_get_accessibility_tcc(self):
        for case_id, case in self.sd.cases().items():
            p = AccessibilityTccParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            for item in result:
                self.assertTrue('db_table' in item)
                self.assertTrue('datetime' in item)


if __name__ == '__main__':
    unittest.main()
