import os
import unittest

from sysdiagnose.parsers.wifinetworks import WifiNetworksParser
from tests import SysdiagnoseTestCase


class TestParsersWifiNetworks(SysdiagnoseTestCase):
    def test_parsewifinetwork(self):
        for case_id, _case in self.sd.cases().items():
            p = WifiNetworksParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            if not files:
                self.skipTest(f"No log files found for {case_id}")

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            self.assertTrue(len(result) > 0)
            # not sure what to assert here as there's not always a result
            # if result:
            #     for key in result.keys():
            #         print(key)
            #         # self.assertTrue(key.startswith('wifi.network'))
            #         break
            self.assert_result_summary_consistent(p, result)


if __name__ == "__main__":
    unittest.main()
