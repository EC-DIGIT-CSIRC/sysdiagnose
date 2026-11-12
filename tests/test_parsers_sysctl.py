import os
import unittest
from datetime import UTC, datetime

from sysdiagnose.parsers.sysctl import SysctlParser
from sysdiagnose.utils.summary import ExecutionStatus
from tests import SysdiagnoseTestCase


class TestParsersSysCtl(SysdiagnoseTestCase):
    def test_get_sysctl(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                p = SysctlParser(self.sd.config, case=_case)
                if not p.is_compatible():
                    self.skipTest(f"Parser {p.module_name} not compatible with iOS {_case.get('ios_version')}")

                files = p.get_log_files()
                if not files:
                    self.skipTest(
                        f"No log files found for {case_id}: parser {p.module_name}, iOS {_case.get('ios_version')}"
                    )

                p.save_result(force=True)
                self.assertTrue(os.path.isfile(p.output_file))

                result = p.get_result()
                for item in result:
                    self.assert_has_required_fields_jsonl(item)
                self.assert_result_summary_consistent(p, result)

    def test_valid_lines(self):
        lines = [
            "security.mac.lockdown_mode_state : 0",
        ]
        p = SysctlParser(self.sd.config, case={"case_id": "test"})
        p.sysdiagnose_creation_datetime = datetime.fromtimestamp(1, tz=UTC)
        result = p.parse_lines(lines)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["data"]["security.mac.lockdown_mode_state"], "0")

    def test_unknown_line(self):
        lines = ["foo : bar : hello", "foo bar hello world"]
        p = SysctlParser(self.sd.config, case={"case_id": "test"})
        p.sysdiagnose_creation_datetime = datetime.fromtimestamp(1, tz=UTC)
        for line in lines:
            # assert an problem is detected is raised
            p.parse_lines([line])
            self.assertEqual(p.get_result_summary().status, ExecutionStatus.ERROR)


if __name__ == "__main__":
    unittest.main()
