from sysdiagnose.parsers.psthread import PsThreadParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersPsthread(SysdiagnoseTestCase):

    def test_parse_psthread(self):
        for case_id, case in self.sd.cases().items():
            p = PsThreadParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            if result:  # not all logs contain data
                for item in result:
                    self.assertTrue('command' in item['data'])
                    self.assertTrue('pid' in item['data'])
                    self.assertTrue('user' in item['data'])
                    self.assert_has_required_fields_jsonl(item)


if __name__ == '__main__':
    unittest.main()
