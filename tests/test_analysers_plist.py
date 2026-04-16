import os
import unittest

from sysdiagnose.analysers.plist import PListAnalyzer
from tests import SysdiagnoseTestCase


class TestAnalysersPList(SysdiagnoseTestCase):
    def test_analyse_list(self):
        for case_id, _case in self.sd.cases().items():
            print(f"Running PListAnalyser for {case_id}")
            # run the analyser
            a = PListAnalyzer(self.sd.config, case_id=case_id)
            a.save_result(force=True)

            self.assertTrue(os.path.isfile(a.output_file))
            self.assertTrue(os.path.getsize(a.output_file) > 0)

            result = a.get_result()
            for item in result:
                self.assert_has_required_fields_jsonl(item)
                self.assertTrue('source' in item['data'])


if __name__ == '__main__':
    unittest.main()
