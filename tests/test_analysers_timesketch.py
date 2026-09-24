import os
import unittest

from sysdiagnose.analysers.timesketch import TimesketchAnalyser
from tests import SysdiagnoseTestCase


class TestAnalysersTimesketch(SysdiagnoseTestCase):
    def test_analyse_timesketch(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                print(f"Running Timesketch export for {case_id}")
                a = TimesketchAnalyser(self.sd.config, case=_case)

                if not a.is_compatible():
                    self.skipTest(f"Analyser {a.module_name} not compatible with iOS {_case.get('ios_version')}")

                a.save_result(force=True)
                self.assertTrue(os.path.isfile(a.output_file))
                self.assertTrue(os.path.getsize(a.output_file) > 0)

                result = a.get_result()
                for item in result:
                    self.assert_has_required_fields_jsonl(item)
                    self.assertIn("data_type", item)
                self.assert_result_summary_consistent(a, result)


if __name__ == "__main__":
    unittest.main()
