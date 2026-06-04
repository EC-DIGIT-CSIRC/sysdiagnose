import os
import unittest

from sysdiagnose.parsers.wifi_known_networks import WifiKnownNetworksParser
from tests import SysdiagnoseTestCase


class TestParsersWifiKnownNetworks(SysdiagnoseTestCase):
    def test_get_known_wifi_networks(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id):
                p = WifiKnownNetworksParser(self.sd.config, case_id=case_id)
                files = p.get_log_files()
                if not files:
                    self.skipTest(f"No log files found for {case_id}")

                p.save_result(force=True)
                self.assertTrue(os.path.isfile(p.output_file))

                result = p.get_result()
                self.assertGreater(len(result), 0)
                self.assert_result_summary_consistent(p, result)


if __name__ == "__main__":
    unittest.main()
