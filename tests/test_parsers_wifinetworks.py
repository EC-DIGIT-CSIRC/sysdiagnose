
from parsers.wifinetworks import parsewifinetwork
from tests import SysdiagnoseTestCase
import os
import unittest


class TestParsersWifiNetworks(SysdiagnoseTestCase):

    log_root_path = 'tests/testdata/iOS15/sysdiagnose_2023.05.24_13-29-15-0700_iPhone-OS_iPhone_19H349/'
    log_files = [
        "WiFi/com.apple.wifi.known-networks.plist",
        "WiFi/com.apple.wifi.plist",
        "WiFi/LEGACY_com.apple.wifi-networks.plist",
        "WiFi/com.apple.wifi-private-mac-networks.plist",
        "WiFi/com.apple.wifi.recent-networks.json"
    ]

    def test_parsewifinetwork(self):
        files = [os.path.join(self.log_root_path, log_file) for log_file in self.log_files]
        result = parsewifinetwork(files)
        self.assertGreater(len(result), 0)
        for log_file in self.log_files:
            end_of_filename = log_file.split('/')[-1]
            self.assertTrue(end_of_filename in result)
            if 'LEGACY' in end_of_filename:  # skip empty file
                continue
            self.assertGreater(len(result[end_of_filename]), 0)


if __name__ == '__main__':
    unittest.main()
