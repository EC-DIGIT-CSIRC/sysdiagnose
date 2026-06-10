import os
import unittest

from sysdiagnose.parsers.itunesstore import ITunesStoreParser
from tests import SysdiagnoseTestCase


class TestParsersIntunesstore(SysdiagnoseTestCase):
    def test_get_itunesstore(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                p = ITunesStoreParser(self.sd.config, case=_case)

                if not p.is_compatible():
                    self.skipTest(f"Parser {p.module_name} not compatible with iOS {_case.get('ios_version')}")

                files = p.get_log_files()
                if not files:
                    # only a few images don't have a db present.
                    # let's keep it failing for now...
                    self.fail(
                        f"No log files found for {case_id}: parser {p.module_name}, iOS {_case.get('ios_version')}"
                    )
                self.assertEqual(len(files), 1)

                p.save_result(force=True)
                self.assertTrue(os.path.isfile(p.output_file))

                result = p.get_result()
                self.assertTrue("application_id" in result)
                self.assertTrue("download" in result)
                self.assertTrue("persistent_manager" in result)
                self.assert_result_summary_consistent(p, result)


if __name__ == "__main__":
    unittest.main()
