from analysers.yarascan import YaraAnalyser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestAnalysersYarascan(SysdiagnoseTestCase):

    def test_analyse_yarascan(self):
        # FIXME we need to first create a yara rule


        for case_id, case in self.sd.cases().items():
            print(f"Running Yarascan for {case_id}")
            # run the analyser
            a = YaraAnalyser(self.sd.config, case_id=case_id)
            a.save_result(force=True)
            self.assertTrue(os.path.isfile(a.output_file))
            self.assertTrue(os.path.getsize(a.output_file) > 0)

            result = a.get_result()
            self.assertGreater(len(result), 0)


if __name__ == '__main__':
    unittest.main()
