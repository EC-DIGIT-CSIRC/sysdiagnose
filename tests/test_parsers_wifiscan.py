from parsers.wifiscan import parse_path, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersWifiScan(SysdiagnoseTestCase):

    def test_parsewifiscan(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            # self.assertTrue(len(files) > 0)  # not all sysdiagnose have wifiscan logs
            for file in files:
                print(f'Parsing {file}')
                result = parse_path(file)
                self.assertGreater(len(result), 0)
                self.assertTrue('total' in result[0])

                for item in result:
                    if 'total' in item:
                        continue
                    self.assertTrue('ssid' in item)


if __name__ == '__main__':
    unittest.main()
