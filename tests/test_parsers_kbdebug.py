from sysdiagnose.parsers.kbdebug import KbdebugParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersSys(SysdiagnoseTestCase):

    def test_parsekbdebug(self):
        for case_id, _case in self.sd.cases().items():
            p = KbdebugParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            self.assertGreater(len(result), 0)
            for item in result:
                self.assert_has_required_fields_jsonl(item)


if __name__ == '__main__':
    unittest.main()
