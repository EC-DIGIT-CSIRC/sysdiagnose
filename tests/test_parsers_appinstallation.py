from sysdiagnose.parsers.appinstallation import AppInstallationParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersAppinstallation(SysdiagnoseTestCase):

    def test_get_appinstallation(self):
        for case_id, case in self.sd.cases().items():
            p = AppInstallationParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()

            if not files:
                continue

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            for item in result:
                self.assertTrue('db_table' in item)
                self.assertTrue('datetime' in item)


if __name__ == '__main__':
    unittest.main()
