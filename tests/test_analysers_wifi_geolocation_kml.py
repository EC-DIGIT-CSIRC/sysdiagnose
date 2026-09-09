import os
import unittest
import xml.etree.ElementTree as ET

from sysdiagnose.analysers.wifi_geolocation_kml import WifiGeolocationKmlAnalyser
from tests import SysdiagnoseTestCase


class TestAnalysersWifiGeolocationKml(SysdiagnoseTestCase):
    def test_analyse_wifi_geolocation_kml(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                a = WifiGeolocationKmlAnalyser(self.sd.config, case=_case)

                if not a.is_compatible():
                    self.skipTest(f"Analyser {a.module_name} not compatible with iOS {_case.get('ios_version')}")

                a.save_result(force=True)
                self.assertTrue(os.path.isfile(a.output_file))
                self.assertTrue(os.path.getsize(a.output_file) > 0)
                self.assert_result_summary_consistent(a, a.get_result())
                # FIXME check for something else within the file...

    def test_generated_kml_is_namespace_well_formed(self):
        """The gx: prefix must be declared, otherwise no conforming XML parser can read the file."""
        kml = WifiGeolocationKmlAnalyser.generate_kml_from_known_networks_json(
            {
                "net1": {
                    "SSID": "test-ssid",
                    "AddedAt": "2023-05-24T13:29:15Z",
                    "Latitude": 1.0,
                    "Longitude": 2.0,
                }
            }
        )
        # on main this raises ParseError: unbound prefix
        root = ET.fromstring(kml)
        self.assertEqual("{http://www.opengis.net/kml/2.2}kml", root.tag)
        self.assertIn("http://www.google.com/kml/ext/2.2", kml)


if __name__ == "__main__":
    unittest.main()
