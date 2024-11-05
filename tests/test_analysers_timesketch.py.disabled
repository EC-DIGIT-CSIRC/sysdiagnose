from sysdiagnose.analysers.timesketch import TimesketchAnalyser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestAnalysersTimesketch(SysdiagnoseTestCase):

    def test_analyse_timsketch(self):
        for case_id, case in self.sd.cases().items():
            print(f"Running Timesketch export for {case_id}")
            a = TimesketchAnalyser(self.sd.config, case_id=case_id)
            a.save_result(force=True)

            self.assertTrue(os.path.isfile(a.output_file))
            self.assertTrue(os.path.getsize(a.output_file) > 0)


if __name__ == '__main__':
    unittest.main()
