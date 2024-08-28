from parsers.appinstallation import AppInstallationParser
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
            self.assertTrue('application' in result)
            self.assertTrue('asset' in result)
            self.assertTrue('client' in result)
            self.assertTrue('download_policy' in result)
            self.assertTrue('download_state' in result)
            self.assertTrue('download' in result)
            self.assertTrue('finished_download' in result)
            self.assertTrue('job_restore' in result)
            self.assertTrue('job_software' in result)
            self.assertTrue('job' in result)
            self.assertTrue('persistent_job' in result)
            self.assertTrue('persistent_manager' in result)
            self.assertTrue('purchase' in result)


if __name__ == '__main__':
    unittest.main()
