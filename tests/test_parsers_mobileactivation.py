from sysdiagnose.parsers.mobileactivation import MobileActivationParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersMobileactivation(SysdiagnoseTestCase):

    def test_mobileactivation(self):
        for case_id, case in self.sd.cases().items():
            p = MobileActivationParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            for item in result:
                self.assertTrue('loglevel' in item['data'])
                self.assertTrue('hexID' in item['data'])
                if item['data']['loglevel'] == 'debug' and 'build_version' in item['data']:
                    self.assertTrue('build_version' in item['data'])
                else:
                    self.assertTrue('message' in item)
                    # self.assertTrue('event_type' in item) # not all logs have event_type
                self.assert_has_required_fields_jsonl(item)


if __name__ == '__main__':
    unittest.main()
