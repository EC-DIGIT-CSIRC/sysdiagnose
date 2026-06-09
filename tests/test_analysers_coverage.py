import os
import unittest

from sysdiagnose.analysers.coverage import CoverageAnalyser
from tests import SysdiagnoseTestCase


class TestAnalysersCoverage(SysdiagnoseTestCase):
    def test_analyse_coverage(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                print(f"Running Coverage for {case_id}")
                # run the analyser
                a = CoverageAnalyser(self.sd.config, case_id=case_id)
                a.save_result(force=True)
                self.assertTrue(os.path.isfile(a.output_file))
                self.assertTrue(os.path.getsize(a.output_file) > 0)

                result = a.get_result()
                self.assertGreater(len(result), 0)
                self.assert_result_summary_consistent(a, result)


if __name__ == "__main__":
    unittest.main()
