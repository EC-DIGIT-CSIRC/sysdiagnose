import json
import unittest

from parsers.wifi_known_networks import getKnownWifiNetworks


class TestParsersWifiKnownNetworks(unittest.TestCase):

    log_path = "tests/testdata/iOS15/sysdiagnose_2023.05.24_13-29-15-0700_iPhone-OS_iPhone_19H349/WiFi/com.apple.wifi.known-networks.plist"

    def test_getKnownWifiNetworks(self):
        known_networks_str = '{"wifi.network.ssid.FIRSTCONWIFI": {"Moving": false, "Hidden": false, "CaptiveProfile": {"IsWhitelistedCaptiveNetwork": false, "CaptiveNetwork": false, "WhitelistedCaptiveNetworkProbeDate": "2023-05-24 19:57:57.912583"}, "JoinedByUserAt": "2023-05-24 19:57:50.247657", "SSID": "b\'FIRSTCONWIFI\'", "AddedAt": "2023-05-24 19:57:50.248702", "__OSSpecific__": {"BEACON_PROBE_INFO_PER_BSSID_LIST": [{"BSSID": "0:13:37:a9:e7:eb", "OTA_SYSTEM_INFO_SENT": false, "OTA_SYSTEM_INFO_BEACON_ONLY_SENT": true}], "CHANNEL_FLAGS": 10, "prevJoined": "2023-05-24 20:14:36.705016", "BSSID": "0:13:37:a9:e7:eb", "CHANNEL": 11, "AP_MODE": 2, "DiagnosticsBssEnv": 1}, "JoinedBySystemAt": "2023-05-24 20:26:05.388462", "SupportedSecurityTypes": "Open", "BSSList": [{"ChannelFlags": 10, "BSSID": "0:13:37:a9:e7:eb", "Channel": 11, "LastAssociatedAt": "2023-05-24 20:26:05.388434"}], "UpdatedAt": "2023-05-24 20:26:05.670268"}}'

        result = getKnownWifiNetworks([self.log_path])
        self.assertGreater(len(result), 0)

        self.assertEqual(json.loads(known_networks_str), result)


if __name__ == '__main__':
    unittest.main()
