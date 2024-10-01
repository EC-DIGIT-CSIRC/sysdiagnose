from sysdiagnose.parsers.itunesstore import iTunesStoreParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersIntunesstore(SysdiagnoseTestCase):

    def test_get_itunesstore(self):
        for case_id, case in self.sd.cases().items():
            p = iTunesStoreParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            if not files:
                continue

            self.assertEqual(len(files), 1)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            self.assertTrue('application_id' in result)
            self.assertTrue('download' in result)
            self.assertTrue('persistent_manager' in result)


if __name__ == '__main__':
    unittest.main()
