from parsers.brctl import parse_path, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersBrctl(SysdiagnoseTestCase):

    def test_parsebrctl(self):
        for log_root_path in self.log_root_paths:
            folders = get_log_files(log_root_path)
            self.assertEqual(len(folders), 1)
            print(f'Parsing {folders}')
            result = parse_path(log_root_path)
            if result:
                self.assertTrue('containers' in result)
                self.assertTrue('boot_history' in result)
                self.assertTrue('server_state' in result)
                self.assertTrue('client_state' in result)
                self.assertTrue('system' in result)
                self.assertTrue('scheduler' in result)
                self.assertTrue('applibrary' in result)
                self.assertTrue('app_library_id' in result)
                self.assertTrue('app_ids' in result)


if __name__ == '__main__':
    unittest.main()
