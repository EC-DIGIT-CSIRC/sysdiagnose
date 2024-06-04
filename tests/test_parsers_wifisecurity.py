from parsers.wifisecurity import parse_path, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersWifiSecurity(SysdiagnoseTestCase):

    def test_get_wifi_security_log(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            self.assertTrue(len(files) > 0)
            print(f'Parsing {files}')
            result = parse_path(log_root_path)
            for item in result:
                self.assertTrue('acct' in item)
                self.assertTrue('agrp' in item)
                self.assertTrue('cdat' in item)
                self.assertTrue('mdat' in item)


if __name__ == '__main__':
    unittest.main()
