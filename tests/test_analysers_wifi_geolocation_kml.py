from sysdiagnose.analysers.wifi_geolocation_kml import WifiGeolocationKmlAnalyser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestAnalysersWifiGeolocationKml(SysdiagnoseTestCase):

    def test_analyse_wifi_geolocation_kml(self):
        for case_id, case in self.sd.cases().items():
            a = WifiGeolocationKmlAnalyser(self.sd.config, case_id=case_id)
            a.save_result(force=True)

            self.assertTrue(os.path.isfile(a.output_file))
            self.assertTrue(os.path.getsize(a.output_file) > 0)

            # FIXME check for something else within the file...


if __name__ == '__main__':
    unittest.main()
