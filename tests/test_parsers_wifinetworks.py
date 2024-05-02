
from parsers.wifinetworks import parsewifinetwork, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersWifiNetworks(SysdiagnoseTestCase):

    def test_parsewifinetwork(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            # self.assertTrue(len(files) > 0)
            print(f'Parsing {files}')
            result = parsewifinetwork(files)
            self.assertGreater(len(result), 0)
            for log_file in files:
                end_of_filename = log_file.split('/')[-1]
                self.assertTrue(end_of_filename in result)


if __name__ == '__main__':
    unittest.main()
