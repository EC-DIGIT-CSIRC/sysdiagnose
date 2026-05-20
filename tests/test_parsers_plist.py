import os
import unittest

from sysdiagnose.parsers.plists import PlistParser
from tests import SysdiagnoseTestCase


class TestParsersPlist(SysdiagnoseTestCase):
    def test_get_plists(self):
        for case_id, _case in self.sd.cases().items():
            p = PlistParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            if not files:
                self.skipTest(f"No log files found for {case_id}")

            p.save_result(force=True)
            self.assertTrue(os.path.isdir(p.output_folder))

            result = p.get_result()
            self.assertGreater(len(result), 0)
            self.assertIn("hidutil.plist", result.keys())
            self.assert_result_summary_consistent(p, result)


if __name__ == "__main__":
    unittest.main()
