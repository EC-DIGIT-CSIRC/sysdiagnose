import os
import unittest

from sysdiagnose.analysers.apps import AppsAnalyser
from tests import SysdiagnoseTestCase


class TestAnalysersApps(SysdiagnoseTestCase):
    def test_analyse_apps(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                # run the analyser
                a = AppsAnalyser(self.sd.config, case=_case)

                if not a.is_compatible():
                    self.skipTest(f"Analyser {a.module_name} not compatible with iOS {_case.get('ios_version')}")

                a.save_result(force=True)
                self.assertTrue(os.path.isfile(a.output_file))
                self.assertTrue(os.path.getsize(a.output_file) > 0)
                result = a.get_result()
                self.assertGreater(len(result), 0)
                self.assert_result_summary_consistent(a, result)


if __name__ == "__main__":
    unittest.main()
