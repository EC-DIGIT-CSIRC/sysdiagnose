from parsers.networkextension import parse_path, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersNetworkExtension(SysdiagnoseTestCase):

    def test_networkextension(self):
        for log_root_path in self.log_root_paths:
            files = [log_file for log_file in get_log_files(log_root_path)]
            print(f'Parsing {files}')
            result = parse_path(log_root_path)
            # TODO below needs to be changed if https://github.com/ydkhatri/nska_deserialize/pull/3 is merged
            # self.assertTrue('Version' in result)
            seen = False
            for entry in result:
                if 'Version' in entry:
                    seen = True
                    break
            self.assertTrue(seen)


if __name__ == '__main__':
    unittest.main()
