from sysdiagnose.parsers.wifisecurity import WifiSecurityParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersWifiSecurity(SysdiagnoseTestCase):

    def test_get_wifi_security_log(self):
        for case_id, case in self.sd.cases().items():
            p = WifiSecurityParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            if not files:
                continue

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            for item in result:
                self.assertTrue('acct' in item['data'])
                self.assertTrue('agrp' in item['data'])
                self.assertTrue('cdat' in item['data'])
                self.assertTrue('mdat' in item['data'])
                self.assert_has_required_fields_jsonl(item)


if __name__ == '__main__':
    unittest.main()
