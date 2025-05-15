from sysdiagnose.parsers.avconference_callsettings import AvConferenceCallSettingsParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersAvConferenceCallSettings(SysdiagnoseTestCase):

    def test_parse_avconverence(self):
        for case_id, case in self.sd.cases().items():
            p = AvConferenceCallSettingsParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()  # noqa F841

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            for item in result:
                self.assert_has_required_fields_jsonl(item)


if __name__ == '__main__':
    unittest.main()
