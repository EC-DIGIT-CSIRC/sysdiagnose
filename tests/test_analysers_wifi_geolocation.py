import os
import unittest
from datetime import datetime

from sysdiagnose.analysers.wifi_geolocation import WifiGeolocationAnalyser
from tests import SysdiagnoseTestCase


class TestAnalysersWifiGeolocation(SysdiagnoseTestCase):
    def test_analyse_wifi_geolocation(self):
        for case_id, _case in self.sd.cases().items():
            a = WifiGeolocationAnalyser(self.sd.config, case_id=case_id)
            a.save_result(force=True)

            self.assertTrue(os.path.isfile(a.output_file))
            self.assertTrue(os.path.getsize(a.output_file) > 0)
            self.assertTrue(os.path.isfile(a.summary_file))

            summary = a.get_result_summary()
            self.assertGreaterEqual(summary.num_events, 1)
            self.assertIsInstance(summary.start_time, datetime)
            self.assertIsNotNone(summary.duration)


if __name__ == "__main__":
    unittest.main()
