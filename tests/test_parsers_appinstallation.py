import os
import unittest

from sysdiagnose.parsers.appinstallation import AppInstallationParser
from tests import SysdiagnoseTestCase


class TestParsersAppinstallation(SysdiagnoseTestCase):
    def test_get_appinstallation(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                p = AppInstallationParser(self.sd.config, case=_case)
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
                    self.assertTrue("db_table" in item)
                    self.assert_has_required_fields_jsonl(item)
                self.assert_result_summary_consistent(p, result)


if __name__ == "__main__":
    unittest.main()
