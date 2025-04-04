from sysdiagnose.analysers.file_stats import FileStatisticsAnalyser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestFileStatisticsAnalyser(SysdiagnoseTestCase):
    def test_analyse_file_stats(self):
        for case_id, case in self.sd.cases().items():
            print(f"Running FileStatisticsAnalyser for {case_id}")
            # run the analyser
            a = FileStatisticsAnalyser(self.sd.config, case_id=case_id)
            a.save_result(force=True)

            self.assertTrue(os.path.isfile(a.output_file))
            self.assertTrue(os.path.getsize(a.output_file) > 0)

            result = a.get_result()
            # device info
            self.assertTrue('os_version' in result[0])
            self.assertTrue('build' in result[0])
            self.assertTrue('product_name' in result[0])
            self.assertTrue('product_type' in result[0])
            # file stats
            for item in result[1]:
                self.assertTrue('folder_name' in item)
                self.assertTrue('file_count' in item)
                self.assertTrue('files' in item)
                for file in item['files']:
                    self.assertTrue('filename' in file)
                    self.assertTrue('extension' in file)
                    self.assertTrue('file_type' in file)


if __name__ == '__main__':
    unittest.main()
