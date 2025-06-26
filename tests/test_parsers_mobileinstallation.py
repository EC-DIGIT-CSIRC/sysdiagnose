from sysdiagnose.parsers.mobileinstallation import MobileInstallationParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersMobileinstallation(SysdiagnoseTestCase):

    def test_mobileinstallation(self):
        for case_id, case in self.sd.cases().items():
            p = MobileInstallationParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            for item in result:
                self.assertTrue('loglevel' in item['data'])
                self.assertTrue('hexID' in item['data'])
                self.assert_has_required_fields_jsonl(item)
                # self.assertTrue('event_type' in item) # not all logs have event_type


if __name__ == '__main__':
    unittest.main()
