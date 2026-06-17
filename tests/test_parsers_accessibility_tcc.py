import os
import unittest

from sysdiagnose.parsers.accessibility_tcc import AccessibilityTccParser
from tests import SysdiagnoseTestCase


class TestParsersAccessibilityTcc(SysdiagnoseTestCase):
    def test_get_accessibility_tcc(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                p = AccessibilityTccParser(self.sd.config, case=_case)
                if not p.is_compatible():
                    self.skipTest(f"Parser {p.module_name} not compatible with iOS {_case.get('ios_version')}")

                files = p.get_log_files()
                if not files:
                    self.fail(
                        f"No log files found for {case_id}: parser {p.module_name}, iOS {_case.get('ios_version')}"
                    )

                p.save_result(force=True)
                self.assertTrue(os.path.isfile(p.output_file))

                result = p.get_result()
                for item in result:
                    self.assertTrue("apollo_module" in item["data"])
                    self.assert_has_required_fields_jsonl(item)
                self.assert_result_summary_consistent(p, result, allow_errors=True)


if __name__ == "__main__":
    unittest.main()
