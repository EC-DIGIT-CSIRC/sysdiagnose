import os
import unittest

from sysdiagnose.parsers.olddsc import OldDscParser
from tests import SysdiagnoseTestCase


class TestParsersOlddsc(SysdiagnoseTestCase):

    def test_parse_olddsc_file(self):
        for case_id, _case in self.sd.cases().items():
            p = OldDscParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            for item in result:
                self.assertTrue('Load_Address' in item['data'])
                self.assert_has_required_fields_jsonl(item)


if __name__ == '__main__':
    unittest.main()
