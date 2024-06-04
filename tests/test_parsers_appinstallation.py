from parsers.appinstallation import parse_path, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersAppinstallation(SysdiagnoseTestCase):

    def test_get_appinstallation(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            print(f'Parsing {files}')
            if not files:
                continue
            self.assertEqual(len(files), 1)
            result = parse_path(log_root_path)
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
