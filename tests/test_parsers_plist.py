import os
import unittest

from sysdiagnose.parsers.plists import PlistParser
from tests import SysdiagnoseTestCase


class TestParsersPlist(SysdiagnoseTestCase):

    def test_get_plists(self):
        for case_id, _case in self.sd.cases().items():
            p = PlistParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            # first run to store in memory
            result = p.get_result()

            p.save_result(force=True)
            self.assertTrue(os.path.isdir(p.output_folder))
            self.assertTrue(os.path.isfile(p.summary_file))

            self.assertGreater(len(result), 0)
            print(result.keys())
            self.assertIn('hidutil.plist', result.keys())
            summary = p.get_result_summary()
            self.assertGreater(summary.num_events, 0)
            self.assertIsNotNone(summary.start_time)
            self.assertIsNotNone(summary.duration)
            # nothing specific to assert here as there's not always a result
            # just catching exceptions


if __name__ == '__main__':
    unittest.main()
