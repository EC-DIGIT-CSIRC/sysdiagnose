import os
import unittest

from sysdiagnose.parsers.mobileinstallation import MobileInstallationParser
from tests import SysdiagnoseTestCase


class TestParsersMobileinstallation(SysdiagnoseTestCase):

    def test_mobileinstallation(self):
        for case_id, _case in self.sd.cases().items():
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


if __name__ == '__main__':
    unittest.main()
