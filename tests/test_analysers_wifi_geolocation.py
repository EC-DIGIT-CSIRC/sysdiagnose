import os
import unittest

from sysdiagnose.analysers.wifi_geolocation import WifiGeolocationAnalyser
from tests import SysdiagnoseTestCase


class TestAnalysersWifiGeolocation(SysdiagnoseTestCase):
    def test_analyse_wifi_geolocation(self):
        for case_id, _case in self.sd.cases().items():
            a = WifiGeolocationAnalyser(self.sd.config, case_id=case_id)
            a.save_result(force=True)

            self.assertTrue(os.path.isfile(a.output_file))
            self.assertTrue(os.path.getsize(a.output_file) > 0)
            self.assert_result_summary_consistent(a, a.get_result())


if __name__ == "__main__":
    unittest.main()
