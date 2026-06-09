import os
import unittest

from sysdiagnose.parsers.transparency import TransparencyParser
from sysdiagnose.parsers.transparency_json import TransparencyJsonParser
from tests import SysdiagnoseTestCase


class TestParsersTransparency(SysdiagnoseTestCase):
    def test_transparency(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                p = TransparencyParser(self.sd.config, case_id=case_id)
                files = p.get_log_files()

                if not files:
                    self.fail(
                        f"No log files found for {case_id}: parser {p.module_name}, iOS {_case.get('ios_version')}"
                    )
                    self.skipTest(f"No log files found for {case_id}")

                p.save_result(force=True)
                self.assertTrue(os.path.isfile(p.output_file))

                p.get_result()
                result = p.get_result()
                for item in result:
                    self.assert_has_required_fields_jsonl(item)

    def test_transparency_json(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                p = TransparencyJsonParser(self.sd.config, case_id=case_id)
                files = p.get_log_files()

                if not files:
                    self.fail(
                        f"No log files found for {case_id}: parser {p.module_name}, iOS {_case.get('ios_version')}"
                    )
                    self.skipTest(f"No log files found for {case_id}")

                p.save_result(force=True)
                self.assertTrue(os.path.isfile(p.output_file))

                result = p.get_result()
                self.assertTrue("copy_status_version" in result)
                self.assertGreater(len(result), 0)
                self.assert_result_summary_consistent(p, result)


if __name__ == "__main__":
    unittest.main()
