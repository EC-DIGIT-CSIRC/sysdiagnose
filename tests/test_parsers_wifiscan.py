from sysdiagnose.parsers.wifiscan import WifiScanParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersWifiScan(SysdiagnoseTestCase):

    def test_parsewifiscan(self):
        for case_id, case in self.sd.cases().items():
            p = WifiScanParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            self.assertGreater(len(result), 0)
            self.assertTrue('total' in result[0])

            for item in result:
                if 'total' in item:
                    continue
                self.assertTrue('ssid' in item)

    def test_parse_summary(self):
        line = 'total=13, 6GHz(PSC)=0, 6GHz(NonPSC)=0, 5GHz(Active)=2, 5GHz(DFS)=0, 2GHz=11, ibss=0, hidden=1, passpoint=0, ph=0, airport=0'
        expected_result = {
            'total': '13',
            '6GHz(PSC)': '0', '6GHz(NonPSC)': '0',
            '5GHz(Active)': '2', '5GHz(DFS)': '0',
            '2GHz': '11', 'ibss': '0',
            'hidden': '1', 'passpoint': '0',
            'ph': '0', 'airport': '0'
        }
        result = WifiScanParser.parse_summary(line)
        self.assertDictEqual(expected_result, result)

    def test_parse_line(self):
        lines = [
            "'FIRSTCONWIFI' (4649525354434f4e57494649), bssid=<redacted>, channel=[11 (flags=0xA, 2GHz, 20MHz)], cc=FR, phy=n (0x10), rssi=-31, rsn=(null), wpa=(null), wapi=no, wep=no, ibss=no, ph=no, swap=no, hs20=no, age=0ms, match=[(null)]",
            "(null) - ssid=(null), shortSSID=0, bssid=12:34:56:78:90:ab, security=wpa2-personal, channel=[5g36/80 (0x410)], cc=BE, phy=n/ac (0x90), rssi=-66, rsn=[mcast=aes_ccm, bip=none, ucast={ aes_ccm }, auths={ psk }, mfp=no, caps=0x0], wpa=(null), wapi=no, wep=no, 6e=no, filsd=no, ibss=no, ph=no, swap=no, hs20=no, age=0ms, match=[(null)]",
            "'FIRSTCONWIFI' <46495253 54434f4e 57494649>, bssid=12:34:56:78:90:ab, channel=[6 (20 MHz, Active)], cc=(null), type=11ac, rssi=-62, rsn=[mcast=aes_ccm, ucast={ aes_ccm }, auths={ psk }, caps=0xc, wpa=(null), wep=no, ibss=no, ph=no, swap=no, hs20=no,",
            "bssid=aa:bb:cc:dd:ee:01, security=wpa2-personal, rsn=[mcast=aes_ccm, bip=none, ucast={ aes_ccm }, auths={ psk }, mfp=no, caps=0x0], channel=2g11/20, phy=n, rssi=-81, wasConnectedDuringSleep=0, bi=100, age=2069ms (244355645)",
        ]
        expected_results = [
            {'ssid': 'FIRSTCONWIFI', 'ssid_hex': '4649525354434f4e57494649',
             'bssid': '<redacted>', 'channel': '11 (flags=0xA, 2GHz, 20MHz)',
             'cc': 'FR', 'phy': 'n (0x10)', 'rssi': '-31', 'rsn': '(null)',
             'wpa': '(null)', 'wapi': 'no', 'wep': 'no', 'ibss': 'no', 'ph': 'no',
             'swap': 'no', 'hs20': 'no', 'age': '0ms', 'match': '(null)'},
            {'ssid': '(null)', 'ssid_hex': '(null)', 'shortSSID': '0',
             'bssid': '12:34:56:78:90:ab', 'security': 'wpa2-personal', 'channel': '5g36/80 (0x410)',
             'cc': 'BE', 'phy': 'n/ac (0x90)', 'rssi': '-66', 'rsn': 'mcast=aes_ccm, bip=none, ucast={ aes_ccm }, auths={ psk }, mfp=no, caps=0x0',
             'wpa': '(null)', 'wapi': 'no', 'wep': 'no', '6e': 'no', 'filsd': 'no', 'ibss': 'no', 'ph': 'no',
             'swap': 'no', 'hs20': 'no', 'age': '0ms', 'match': '(null)'},
            {'ssid': 'FIRSTCONWIFI', 'ssid_hex': '4649525354434f4e57494649',
             'bssid': '12:34:56:78:90:ab', 'channel': '6 (20 MHz, Active)',
             'cc': '(null)', 'type': '11ac', 'rssi': '-62', 'rsn': 'mcast=aes_ccm, ucast={ aes_ccm }, auths={ psk }, caps=0xc, wpa=(null), wep=no, ibss=no, ph=no, swap=no, hs20=no,'},
            {'ssid': '<unknown>', 'security': 'wpa2-personal',
             'rsn': 'mcast=aes_ccm, bip=none, ucast={ aes_ccm }, auths={ psk }, mfp=no, caps=0x0',
             'channel': '2g11/20', 'phy': 'n', 'rssi': '-81', 'wasConnectedDuringSleep': '0', 'bi': '100', 'age': '2069ms (244355645)'},
        ]
        for line, expected_result in zip(lines, expected_results, strict=True):
            result = WifiScanParser.parse_line(line)
            self.assertDictEqual(expected_result, result)


if __name__ == '__main__':
    unittest.main()
