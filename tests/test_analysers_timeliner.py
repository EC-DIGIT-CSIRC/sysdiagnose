from analysers.timeliner import TimelinerAnalyser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestAnalysersTimeliner(SysdiagnoseTestCase):

    def test_analyse_timeliner(self):
        for case_id, case in self.sd.cases().items():
            print(f"Running Timeliner for {case_id}")
            a = TimelinerAnalyser(self.sd.config, case_id=case_id)
            a.save_result(force=True)

            self.assertTrue(os.path.isfile(a.output_file))
            self.assertTrue(os.path.getsize(a.output_file) > 0)


if __name__ == '__main__':
    unittest.main()
