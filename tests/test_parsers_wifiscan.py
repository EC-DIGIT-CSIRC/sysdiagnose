import os
import unittest

from parsers.wifiscan import parsewifiscan


class TestParsersWifiScan(unittest.TestCase):

    log_root_path = 'tests/testdata/iOS15/sysdiagnose_2023.05.24_13-29-15-0700_iPhone-OS_iPhone_19H349/'
    log_files = [
        "WiFi/wifi_scan.txt"
    ]

    def test_parsewifiscan(self):
        files = [os.path.join(self.log_root_path, log_file) for log_file in self.log_files]
        result = parsewifiscan(files)
        self.assertGreater(len(result), 0)
        self.assertTrue('total' in result[0])

        for item in result:
            if 'total' in item:
                continue
            self.assertTrue('ssid' in item)


if __name__ == '__main__':
    unittest.main()
