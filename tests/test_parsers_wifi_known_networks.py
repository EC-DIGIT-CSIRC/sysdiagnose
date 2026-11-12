import os
import unittest

from sysdiagnose.parsers.wifi_known_networks import WifiKnownNetworksParser
from tests import SysdiagnoseTestCase


class TestParsersWifiKnownNetworks(SysdiagnoseTestCase):
    def test_get_known_wifi_networks(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                p = WifiKnownNetworksParser(self.sd.config, case=_case)

                if not p.is_compatible():
                    self.skipTest(f"Parser {p.module_name} not compatible with iOS {_case.get('ios_version')}")

                files = p.get_log_files()
                if not files:
                    # may not have the file
                    self.skipTest(
                        f"No log files found for {case_id}: parser {p.module_name}, iOS {_case.get('ios_version')}"
                    )

                p.save_result(force=True)
                result = p.get_result()
                self.assert_result_summary_consistent(p, result)

                self.assertTrue(os.path.isfile(p.output_file))

                self.assertGreater(len(result), 0)


if __name__ == "__main__":
    unittest.main()
