from parsers.mobileactivation import parsemobactiv, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersMobileinstallation(SysdiagnoseTestCase):

    def test_mobileactivation(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            for file in files:
                print(f'Parsing {file}')
                result = parsemobactiv([file])
                for item in result['events']:
                    self.assertTrue('timestamp' in item)
                    self.assertTrue('loglevel' in item)
                    self.assertTrue('hexID' in item)
                    if item['loglevel'] == 'debug' and 'build_version' in item:
                        self.assertTrue('build_version' in item)
                        self.assertTrue('internal_build' in item)
                        self.assertTrue('product_type' in item)
                        self.assertTrue('device_class' in item)
                    else:
                        self.assertTrue('msg' in item)
                        # self.assertTrue('event_type' in item) # not all logs have event_type


if __name__ == '__main__':
    unittest.main()
