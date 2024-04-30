from parsers.wifiscan import parsewifiscan
from tests import SysdiagnoseTestCase
import os
import unittest


class TestParsersWifiScan(SysdiagnoseTestCase):

    log_files = [
        "WiFi/wifi_scan.txt"
    ]
    # self.log_root_paths is defined in SysdiagnoseTestCase

    def test_parsewifiscan(self):
        for log_root_path in self.log_root_paths:
            files = [os.path.join(log_root_path, log_file) for log_file in self.log_files]
            for file in files:
                print(f'Parsing {file}')
                result = parsewifiscan([file])
                self.assertGreater(len(result), 0)
                self.assertTrue('total' in result[0])

                for item in result:
                    if 'total' in item:
                        continue
                    self.assertTrue('ssid' in item)


if __name__ == '__main__':
    unittest.main()
