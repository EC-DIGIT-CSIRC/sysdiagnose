from parsers.accessibility_tcc import parse_path, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersAccessibilityTcc(SysdiagnoseTestCase):

    def test_get_accessibility_tcc(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            for file in files:
                print(f'Parsing {file}')
                result = parse_path(file)
                self.assertTrue('admin' in result)
                self.assertTrue('policies' in result)
                self.assertTrue('active_policy' in result)
                self.assertTrue('access_overrides' in result)
                self.assertTrue('expired' in result)
                self.assertTrue('access' in result)


if __name__ == '__main__':
    unittest.main()
