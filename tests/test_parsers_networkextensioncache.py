from parsers.networkextensioncache import parse_path, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersNetworkExtensionCache(SysdiagnoseTestCase):

    def test_networkextensioncache(self):
        for log_root_path in self.log_root_paths:
            files = [log_file for log_file in get_log_files(log_root_path)]
            for file in files:
                print(f'Parsing {file}')
                result = parse_path(file)
                self.assertGreater(len(result), 0)


if __name__ == '__main__':
    unittest.main()
