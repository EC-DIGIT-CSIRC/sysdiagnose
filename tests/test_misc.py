from tests import SysdiagnoseTestCase
import misc
import unittest


class TestMisc(SysdiagnoseTestCase):

    def test_load_plist_with_binary_file(self):
        result = misc.load_plist_file_as_json("tests/testdata/iOS15/sysdiagnose_2023.05.24_13-29-15-0700_iPhone-OS_iPhone_19H349/WiFi/com.apple.wifi.known-networks.plist")
        self.assertGreater(len(result), 0)
        self.assertTrue(result['wifi.network.ssid.FIRSTCONWIFI'])

    def test_load_plist_with_json_file(self):
        result = misc.load_plist_file_as_json("tests/testdata/iOS15/sysdiagnose_2023.05.24_13-29-15-0700_iPhone-OS_iPhone_19H349/logs/SystemVersion/SystemVersion.plist")
        self.assertGreater(len(result), 0)
        self.assertTrue(result['ProductName'])
        self.assertTrue(result['ProductBuildVersion'])
        self.assertTrue(result['ProductVersion'])
        self.assertTrue(result['BuildID'])
        self.assertTrue(result['SystemImageID'])


if __name__ == '__main__':
    unittest.main()
