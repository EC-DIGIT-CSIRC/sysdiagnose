from sysdiagnose.parsers.plists import PlistParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersPlist(SysdiagnoseTestCase):

    def test_get_plists(self):
        for case_id, case in self.sd.cases().items():
            p = PlistParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            # first run to store in memory
            result = p.get_result()

            p.save_result(force=True)
            self.assertTrue(os.path.isdir(p.output_folder))

            self.assertGreater(len(result), 0)
            print(result.keys())
            self.assertIn('hidutil.plist', result.keys())
            # nothing specific to assert here as there's not always a result
            # just catching exceptions


if __name__ == '__main__':
    unittest.main()
