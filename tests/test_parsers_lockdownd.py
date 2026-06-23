import os
import unittest
from datetime import timedelta, timezone

from sysdiagnose.parsers.lockdownd import LockdowndParser
from tests import SysdiagnoseTestCase


class TestParsersLockdownd(SysdiagnoseTestCase):
    tzinfo = timezone(timedelta(hours=1))

    def test_parse_lockdownd(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                p = LockdowndParser(self.sd.config, case=_case)

                if not p.is_compatible():
                    self.skipTest(f"Parser {p.module_name} not compatible with iOS {_case.get('ios_version')}")

                files = p.get_log_files()
                if not files:
                    self.fail(
                        f"No log files found for {case_id}: parser {p.module_name}, iOS {_case.get('ios_version')}"
                    )

                p.save_result(force=True)
                self.assertTrue(os.path.isfile(p.output_file))

                result = p.get_result()
                for item in result:
                    self.assert_has_required_fields_jsonl(item)
                self.assert_result_summary_consistent(p, result)

    def test_parse_lockdownd_simple(self):
        input = [
            "05/24/23 13:55:38.410307 pid=76 mglog: libMobileGestalt utility.c:70: Could not open /private/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist: No such file or directory",
            "05/24/23 13:55:38.453538 pid=76 data_ark_set_block_invoke: dirtied by changing -HasSiDP",
            "05/24/23 13:55:45.978543 pid=76 lockstart_local: Build version: 19H349",
        ]
        expected_result = [
            {
                "datetime": "2023-05-24T13:55:38.410307+01:00",
                "timestamp_desc": "lockdownd mglog",
                "module": "TestModule",
                "data": {"pid": 76, "event_type": "mglog"},
                "message": "libMobileGestalt utility.c:70: Could not open /private/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist: No such file or directory",
            },
            {
                "datetime": "2023-05-24T13:55:38.453538+01:00",
                "timestamp_desc": "lockdownd data_ark_set_block_invoke",
                "module": "TestModule",
                "data": {"pid": 76, "event_type": "data_ark_set_block_invoke"},
                "message": "dirtied by changing -HasSiDP",
            },
            {
                "datetime": "2023-05-24T13:55:45.978543+01:00",
                "timestamp_desc": "lockdownd lockstart_local",
                "module": "TestModule",
                "data": {"pid": 76, "event_type": "lockstart_local"},
                "message": "Build version: 19H349",
            },
        ]
        result = LockdowndParser.extract_from_list(input, tzinfo=self.tzinfo, module="TestModule")
        self.maxDiff = None
        self.assertEqual(result, expected_result)

    def test_parse_lockdownd_multiline(self):
        input = [
            "05/24/23 13:55:45.978543 pid=76 lockstart_local: Build version: 19H349",
            "hello world",
            "05/24/23 13:55:45.978543 pid=76 lockstart_local: Build version: 19H349",
        ]

        expected_result = [
            {
                "datetime": "2023-05-24T13:55:45.978543+01:00",
                "timestamp_desc": "lockdownd lockstart_local",
                "module": "TestModule",
                "data": {"pid": 76, "event_type": "lockstart_local"},
                "message": "Build version: 19H349hello world",
            },
            {
                "datetime": "2023-05-24T13:55:45.978543+01:00",
                "timestamp_desc": "lockdownd lockstart_local",
                "module": "TestModule",
                "data": {"pid": 76, "event_type": "lockstart_local"},
                "message": "Build version: 19H349",
            },
        ]
        result = LockdowndParser.extract_from_list(input, tzinfo=self.tzinfo, module="TestModule")
        self.maxDiff = None
        self.assertEqual(result, expected_result)


if __name__ == "__main__":
    unittest.main()
