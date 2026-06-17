import json
import os
import tempfile
import unittest

from sysdiagnose.parsers.logarchive import LogarchiveHelper, LogarchiveParser
from tests import SysdiagnoseTestCase


class TestParsersLogarchive(SysdiagnoseTestCase):
    def test_parse_logarchive(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                p = LogarchiveParser(self.sd.config, case=_case)

                if not p.is_compatible():
                    self.skipTest(f"Parser {p.module_name} not compatible with iOS {_case.get('ios_version')}")

                files = p.get_log_files()
                if not files:
                    self.fail(
                        f"No log files found for {case_id}: parser {p.module_name}, iOS {_case.get('ios_version')}"
                    )

                p.save_result(force=True)
                self.assertTrue(os.path.isfile(p.output_file))

                # validate first line structure without loading entire file
                with open(p.output_file) as f:
                    item = json.loads(f.readline())
                    self.assertIn("subsystem", item["data"])
                    self.assert_has_required_fields_jsonl(item)

                # count lines to validate summary without materializing full result
                with open(p.output_file) as f:
                    num_lines = sum(1 for _ in f)
                self.assert_result_summary_consistent(p, [None] * num_lines)

    def test_convert_native_time_to_unifiedlog(self):
        input = "2023-05-24 13:03:28.908085-0700"
        expected_output = 1684958608908084992
        result = LogarchiveHelper.convert_native_time_to_unifiedlog_format(input)
        self.assertEqual(result, expected_output)

        input = "2023-05-24 20:03:28.908085-0000"
        expected_output = 1684958608908084992
        result = LogarchiveHelper.convert_native_time_to_unifiedlog_format(input)
        self.assertEqual(result, expected_output)

    def test_convert_unifiedlog_time_to_datetime(self):
        input = 1684958608908085200
        expected_output = "2023-05-24T20:03:28.908085+00:00"
        result = LogarchiveHelper.convert_unifiedlog_time_to_datetime(input).isoformat(timespec="microseconds")
        self.assertEqual(result, expected_output)

    def test_convert_entry_to_unified(self):
        input = {
            "timezoneName": "",
            "messageType": "Default",
            "eventType": "logEvent",
            "source": None,
            "formatString": "FIPSPOST_KEXT [%llu] %s:%d: PASSED: (%u ms) - fipspost_post_integrity\n",
            "userID": 0,
            "activityIdentifier": 0,
            "subsystem": "",
            "category": "",
            "threadID": 101,
            "senderImageUUID": "A6F4A2BD-5575-37EB-91C0-28AB00C8FCBF",
            "backtrace": {"frames": [{"imageOffset": 6084, "imageUUID": "A6F4A2BD-5575-37EB-91C0-28AB00C8FCBF"}]},
            "bootUUID": "49BA93E4-C511-47A3-B6CC-62D80BFFE539",
            "processImagePath": "/kernel",
            "senderImagePath": "/System/Library/Extensions/corecrypto.kext/corecrypto",
            "timestamp": "2023-05-24 13:03:28.908085-0700",
            "machTimestamp": 161796510,
            "eventMessage": "FIPSPOST_KEXT [161796151] fipspost_post:169: PASSED: (1 ms) - fipspost_post_integrity",
            "processImageUUID": "39395A83-7379-3C29-AB78-D1B5EDB9C714",
            "traceID": 444438921084932,
            "processID": 0,
            "senderProgramCounter": 6084,
            "parentActivityIdentifier": 0,
        }
        expected_output = {
            "data": {
                "timezone_name": "",
                "log_type": "Default",
                "event_type": "logEvent",
                "source": None,
                "raw_message": "FIPSPOST_KEXT [%llu] %s:%d: PASSED: (%u ms) - fipspost_post_integrity\n",
                "euid": 0,
                "activity_id": 0,
                "subsystem": "",
                "category": "",
                "thread_id": 101,
                "library_uuid": "A6F4A2BD557537EB91C028AB00C8FCBF",
                "backtrace": {"frames": [{"imageOffset": 6084, "imageUUID": "A6F4A2BD-5575-37EB-91C0-28AB00C8FCBF"}]},
                "boot_uuid": "49BA93E4C51147A3B6CC62D80BFFE539",
                "process": "/kernel",
                "library": "/System/Library/Extensions/corecrypto.kext/corecrypto",
                "machTimestamp": 161796510,
                "process_uuid": "39395A8373793C29AB78D1B5EDB9C714",
                "traceID": 444438921084932,
                "pid": 0,
                "senderProgramCounter": 6084,
                "parentActivityIdentifier": 0,
            },
            "datetime": "2023-05-24T13:03:28.908085-07:00",
            "message": "FIPSPOST_KEXT [161796151] fipspost_post:169: PASSED: (1 ms) - fipspost_post_integrity",
            "timestamp_desc": "logarchive",
            "module": "logarchive",
        }
        result = LogarchiveHelper.convert_entry_to_unifiedlog_format(input)
        self.maxDiff = None
        self.assertDictEqual(result, expected_output)

    def test_merge_files(self):
        input = []

        input.append(
            [
                {"datetime": "2000-01-01T10:01:00.000000+00:00", "data": "a"},
                {"datetime": "2000-01-01T10:02:00.000000+00:00", "data": "b"},
                {"datetime": "2000-01-01T10:03:00.000000+00:00", "data": "c"},
                {"datetime": "2000-01-01T10:04:00.000000+00:00", "data": "d"},
                {"datetime": "2000-01-01T10:05:00.000000+00:00", "data": "e"},
                {"datetime": "2000-01-01T10:06:00.000000+00:00", "data": "f"},
                {"datetime": "2000-01-01T10:07:00.000000+00:00", "data": "g"},
            ]
        )
        input.append(
            [
                {"datetime": "2000-01-01T10:01:00.000000+00:00", "data": "a-wrong"},
                {"datetime": "2000-01-01T10:02:00.000000+00:00", "data": "b-wrong"},
                {"datetime": "2000-01-01T10:03:00.000000+00:00", "data": "c-wrong"},
                {"datetime": "2000-01-01T10:04:00.000000+00:00", "data": "d-wrong"},
                {"datetime": "2000-01-01T10:05:00.000000+00:00", "data": "e-wrong"},
                {"datetime": "2000-01-01T10:06:00.000000+00:00", "data": "f-wrong"},
                {"datetime": "2000-01-01T10:07:00.000000+00:00", "data": "g-wrong"},
            ]
        )

        input.append(
            [  # should be ignored
                {"datetime": "2000-01-01T10:04:00.000000+00:00", "data": "d-wrong"},
                {"datetime": "2000-01-01T10:05:00.000000+00:00", "data": "e-wrong"},
                {"datetime": "2000-01-01T10:06:00.000000+00:00", "data": "f-wrong"},
            ]
        )
        input.append(
            [  # overlaps first list, so must be taken from the end of first list
                {"datetime": "2000-01-01T10:07:00.000000+00:00", "data": "g-wrong"},
                {"datetime": "2000-01-01T10:08:00.000000+00:00", "data": "h"},
                {"datetime": "2000-01-01T10:09:00.000000+00:00", "data": "i"},
                {"datetime": "2000-01-01T10:10:00.000000+00:00", "data": "j"},
            ]
        )
        input.append(
            [  # small gap
                {"datetime": "2000-01-01T10:12:00.000000+00:00", "data": "k"},
                {"datetime": "2000-01-01T10:13:00.000000+00:00", "data": "l"},
                {"datetime": "2000-01-01T10:14:00.000000+00:00", "data": "m"},
            ]
        )

        expected_output = [
            {"datetime": "2000-01-01T10:01:00.000000+00:00", "data": "a"},
            {"datetime": "2000-01-01T10:02:00.000000+00:00", "data": "b"},
            {"datetime": "2000-01-01T10:03:00.000000+00:00", "data": "c"},
            {"datetime": "2000-01-01T10:04:00.000000+00:00", "data": "d"},
            {"datetime": "2000-01-01T10:05:00.000000+00:00", "data": "e"},
            {"datetime": "2000-01-01T10:06:00.000000+00:00", "data": "f"},
            {"datetime": "2000-01-01T10:07:00.000000+00:00", "data": "g"},
            {"datetime": "2000-01-01T10:08:00.000000+00:00", "data": "h"},
            {"datetime": "2000-01-01T10:09:00.000000+00:00", "data": "i"},
            {"datetime": "2000-01-01T10:10:00.000000+00:00", "data": "j"},
            {"datetime": "2000-01-01T10:12:00.000000+00:00", "data": "k"},
            {"datetime": "2000-01-01T10:13:00.000000+00:00", "data": "l"},
            {"datetime": "2000-01-01T10:14:00.000000+00:00", "data": "m"},
        ]

        temp_files = []
        try:
            # write the files with the test data
            for fname in input:
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_files.append(
                        {
                            "file": temp_file,
                        }
                    )
                    for entry in fname:
                        temp_file.write(json.dumps(entry).encode())
                        temp_file.write(b"\n")
            # merge the files
            with tempfile.NamedTemporaryFile(delete=False) as output_file:
                pass
            LogarchiveHelper.merge_files(temp_files, output_file.name)

            # read the output file
            result = []
            with open(output_file.name) as f:
                for line in f:
                    result.append(json.loads(line))

        finally:
            for temp_file in temp_files:
                os.remove(temp_file["file"].name)
            os.remove(output_file.name)

        self.assertListEqual(result, expected_output)


if __name__ == "__main__":
    unittest.main()
