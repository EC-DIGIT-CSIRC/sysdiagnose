from sysdiagnose.parsers.mobilebackup import MobileBackupParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersBackup(SysdiagnoseTestCase):

    def test_mobilebackup(self):
        for case_id, case in self.sd.cases().items():
            p = MobileBackupParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            if not files:  # we may not have backup
                continue

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            for item in result:
                self.assertTrue('timestamp' in item)


if __name__ == '__main__':
    unittest.main()
