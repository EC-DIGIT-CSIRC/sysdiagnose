from analysers.ps_everywhere import PsEverywhereAnalyser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestAnalysersPsEverywhere(SysdiagnoseTestCase):
    def test_analyse_ps_everywhere(self):
        for case_id, case in self.sd.cases().items():
            print(f"Running PsEverywhereAnalyser for {case_id}")
            # run the analyser
            a = PsEverywhereAnalyser(self.sd.config, case_id=case_id)
            a.save_result(force=True)
            self.assertTrue(os.path.isfile(a.output_file))
            self.assertTrue(os.path.getsize(a.output_file) > 0)

            result = a.get_result()
            self.assertGreater(len(result), 0)


if __name__ == '__main__':
    unittest.main()
