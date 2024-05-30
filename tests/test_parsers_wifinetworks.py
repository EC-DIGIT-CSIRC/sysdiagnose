
from parsers.wifinetworks import parse_path, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersWifiNetworks(SysdiagnoseTestCase):

    def test_parsewifinetwork(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            # self.assertTrue(len(files) > 0)
            for file in files:
                print(f'Parsing {file}')
                parse_path(file)
                # not sure what to assert here as there's not always a result
                # if result:
                #     for key in result.keys():
                #         print(key)
                #         # self.assertTrue(key.startswith('wifi.network'))
                #         break


if __name__ == '__main__':
    unittest.main()
