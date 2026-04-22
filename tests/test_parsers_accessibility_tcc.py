import os
import unittest

from sysdiagnose.parsers.accessibility_tcc import AccessibilityTccParser
from tests import SysdiagnoseTestCase


class TestParsersAccessibilityTcc(SysdiagnoseTestCase):

    def test_get_accessibility_tcc(self):
        for case_id, _case in self.sd.cases().items():
            p = AccessibilityTccParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            for item in result:
                self.assertTrue('apollo_module' in item['data'])
                self.assert_has_required_fields_jsonl(item)


if __name__ == '__main__':
    unittest.main()
