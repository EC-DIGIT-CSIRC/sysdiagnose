import os
import unittest

from sysdiagnose.parsers.avconference_callsettings import AvConferenceCallSettingsParser
from tests import SysdiagnoseTestCase


class TestParsersAvConferenceCallSettings(SysdiagnoseTestCase):
    def test_parse_avconverence(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id):
                p = AvConferenceCallSettingsParser(self.sd.config, case_id=case_id)
                files = p.get_log_files()
                if not files:
                    self.fail(
                        f"No log files found for {case_id}: parser {p.module_name}, iOS {_case.get('ios_version')}"
                    )
                    self.skipTest(f"No log files found for {case_id}")

                p.save_result(force=True)
                self.assertTrue(os.path.isfile(p.output_file))

                result = p.get_result()
                for item in result:
                    self.assert_has_required_fields_jsonl(item)
                self.assert_result_summary_consistent(p, result)


if __name__ == "__main__":
    unittest.main()
