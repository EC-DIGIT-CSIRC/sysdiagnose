from sysdiagnose.parsers.mcsettingsevents import McSettingsEventsParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersMcSettingsEvents(SysdiagnoseTestCase):

    def test_parse_mcsettingsevents(self):
        for case_id, case in self.sd.cases().items():
            p = McSettingsEventsParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            for item in result:
                self.assert_has_required_fields_jsonl(item)


if __name__ == '__main__':
    unittest.main()
