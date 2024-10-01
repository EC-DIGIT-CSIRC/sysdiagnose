from sysdiagnose.parsers.wifiscan import WifiScanParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersWifiScan(SysdiagnoseTestCase):

    def test_parsewifiscan(self):
        for case_id, case in self.sd.cases().items():
            p = WifiScanParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            self.assertGreater(len(result), 0)
            self.assertTrue('total' in result[0])

            for item in result:
                if 'total' in item:
                    continue
                self.assertTrue('ssid' in item)


if __name__ == '__main__':
    unittest.main()
