import os
import unittest

from sysdiagnose.parsers.powerlogs import PowerLogsParser
from tests import SysdiagnoseTestCase


class TestParsersPowerlogs(SysdiagnoseTestCase):

    def test_get_powerlogs(self):
        for case_id, _case in self.sd.cases().items():
            p = PowerLogsParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            if result:  # some files are empty
                for item in result:
                    self.assertTrue('apollo_module' in item['data'])
                    self.assert_has_required_fields_jsonl(item)


if __name__ == '__main__':
    unittest.main()
