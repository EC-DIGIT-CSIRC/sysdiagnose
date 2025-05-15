from sysdiagnose.parsers.battery_bdc import BatteryBDCParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersBatteryBDC(SysdiagnoseTestCase):

    def test_parse(self):
        for case_id, case in self.sd.cases().items():
            p = BatteryBDCParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()  # noqa F841

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            for item in result:
                self.assert_has_required_fields_jsonl(item)


if __name__ == '__main__':
    unittest.main()
