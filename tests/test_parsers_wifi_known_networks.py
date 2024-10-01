from sysdiagnose.parsers.wifi_known_networks import WifiKnownNetworksParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersWifiKnownNetworks(SysdiagnoseTestCase):

    def test_getKnownWifiNetworks(self):
        for case_id, case in self.sd.cases().items():
            p = WifiKnownNetworksParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            self.assertGreater(len(result), 0)


if __name__ == '__main__':
    unittest.main()
