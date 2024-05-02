from parsers.wifi_known_networks import getKnownWifiNetworks, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersWifiKnownNetworks(SysdiagnoseTestCase):

    def test_getKnownWifiNetworks(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            self.assertTrue(len(files) > 0)
            for file in files:
                print(f'Parsing {file}')
                result = getKnownWifiNetworks([file])
                self.assertGreater(len(result), 0)


if __name__ == '__main__':
    unittest.main()
