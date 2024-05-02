from parsers.itunesstore import get_itunesstore, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersIntunesstore(SysdiagnoseTestCase):

    def test_get_itunesstore(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            for file in files:
                print(f'Parsing {file}')
                result = get_itunesstore(file)
                self.assertTrue('application_id' in result)
                self.assertTrue('download' in result)
                self.assertTrue('persistent_manager' in result)


if __name__ == '__main__':
    unittest.main()
