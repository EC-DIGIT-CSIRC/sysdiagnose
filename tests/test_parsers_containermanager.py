from parsers.containermanager import parse_path, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersContainermanager(SysdiagnoseTestCase):

    def test_parsecontainermanager(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            print(f'Parsing {files}')
            result = parse_path(log_root_path)
            for item in result:
                self.assertTrue('timestamp' in item)
                self.assertTrue('loglevel' in item)
                self.assertTrue('hexID' in item)
                self.assertTrue('loglevel' in item)
                self.assertTrue('msg' in item)


if __name__ == '__main__':
    unittest.main()
