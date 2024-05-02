from parsers.mobileinstallation import parsemobinstall, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersMobileinstallation(SysdiagnoseTestCase):

    def test_mobileinstallation(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            for file in files:
                print(f'Parsing {file}')
                result = parsemobinstall([file])
                for item in result['events']:
                    self.assertTrue('timestamp' in item)
                    self.assertTrue('loglevel' in item)
                    self.assertTrue('hexID' in item)
                    self.assertTrue('msg' in item)
                    # self.assertTrue('event_type' in item) # not all logs have event_type


if __name__ == '__main__':
    unittest.main()
