from parsers.networkextension import parse_path, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersNetworkExtension(SysdiagnoseTestCase):

    def test_networkextension(self):
        for log_root_path in self.log_root_paths:
            files = [log_file for log_file in get_log_files(log_root_path)]
            print(f'Parsing {files}')
            result = parse_path(log_root_path)
            self.assertTrue('$objects' in result)


if __name__ == '__main__':
    unittest.main()
