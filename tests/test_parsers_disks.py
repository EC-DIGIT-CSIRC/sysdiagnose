from sysdiagnose.parsers.disks import DisksParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersDisks(SysdiagnoseTestCase):

    def test_parse_disks(self):
        for case_id, case in self.sd.cases().items():
            p = DisksParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            if not files:  # we may not have disks.txt
                continue

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            if result:  # not all logs contain data
                for item in result:
                    self.assertTrue('filesystem' in item['data'] or 'mounted_on' in item['data'])
                    self.assert_has_required_fields_jsonl(item)


if __name__ == '__main__':
    unittest.main()
