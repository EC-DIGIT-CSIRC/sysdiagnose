import os
import unittest

from sysdiagnose.analysers.file_stats import FileStatisticsAnalyser
from tests import SysdiagnoseTestCase


class TestFileStatisticsAnalyser(SysdiagnoseTestCase):
    def test_analyse_file_stats(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                a = FileStatisticsAnalyser(self.sd.config, case_id=case_id)
                a.save_result(force=True)

                self.assertTrue(os.path.isfile(a.output_file))
                self.assertTrue(os.path.getsize(a.output_file) > 0)

                result = a.get_result()
                # device info
                self.assertIn("os_version", result["device_info"])
                self.assertIn("build", result["device_info"])
                self.assertIn("product_name", result["device_info"])
                self.assertIn("product_type", result["device_info"])
                # file stats
                for item in result["file_stats"]:
                    self.assertIn("folder_name", item)
                    self.assertIn("file_count", item)
                    self.assertIn("files", item)
                    for file in item["files"]:
                        self.assertIn("filename", file)
                        self.assertIn("extension", file)
                        self.assertIn("file_type", file)
                self.assert_result_summary_consistent(a, result)


if __name__ == "__main__":
    unittest.main()
