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
            self.assertTrue('admin' in result)
            self.assertTrue('policies' in result)
            self.assertTrue('active_policy' in result)
            self.assertTrue('access_overrides' in result)
            self.assertTrue('expired' in result)
            self.assertTrue('access' in result)


if __name__ == '__main__':
    unittest.main()
