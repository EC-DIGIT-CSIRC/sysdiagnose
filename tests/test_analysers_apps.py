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
                result = a.get_result()

                # Check the summary first so a crash fails with its recorded cause, not "file missing".
                self.assert_result_summary_consistent(a, result)

                # A successful run must have produced a non-empty output file.
                self.assertTrue(os.path.isfile(a.output_file))
                self.assertTrue(os.path.getsize(a.output_file) > 0)
                self.assertGreater(len(result), 0)


if __name__ == "__main__":
    unittest.main()
