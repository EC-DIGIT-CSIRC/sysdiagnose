import os
import unittest

from sysdiagnose.parsers.olddsc import OldDscParser
from tests import SysdiagnoseTestCase


class TestParsersOlddsc(SysdiagnoseTestCase):
    def test_parse_olddsc_file(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get('ios_version')):
                p = OldDscParser(self.sd.config, case_id=case_id)
                files = p.get_log_files()
                if not files:
                    self.fail(
                        f"No log files found for {case_id}: parser {p.module_name}, iOS {_case.get('ios_version')}"
                    )
                    self.skipTest(f"No log files found for {case_id}")

                p.save_result(force=True)
                self.assertTrue(os.path.isfile(p.output_file))

                result = p.get_result()
                for item in result:
                    self.assertTrue("Load_Address" in item["data"])
                    self.assert_has_required_fields_jsonl(item)
                self.assert_result_summary_consistent(p, result)


if __name__ == "__main__":
    unittest.main()
