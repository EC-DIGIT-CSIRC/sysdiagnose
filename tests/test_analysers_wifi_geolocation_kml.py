from analysers.wifi_geolocation_kml import analyse_path
from parsers.wifi_known_networks import parse_path_to_folder, get_log_files
from tests import SysdiagnoseTestCase
import unittest
import os
import tempfile


class TestAnalysersWifiGeolocationKml(SysdiagnoseTestCase):

    def test_analyse_wifi_geolocation_kml(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            self.assertTrue(len(files) > 0)
            with tempfile.TemporaryDirectory() as tmp_outpath:
                parse_path_to_folder(log_root_path, output_folder=tmp_outpath)
                output_file = os.path.join(tmp_outpath, 'wifi_geolocation.kml')
                analyse_path(case_folder=tmp_outpath, output_file=output_file)
                self.assertTrue(os.path.isfile(output_file))
                # FIXME check for something else within the file...


if __name__ == '__main__':
    unittest.main()
