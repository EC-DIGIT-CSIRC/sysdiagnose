from parsers.logarchive import get_log_files, parse_path, parse_path_to_folder, convert_entry_to_unifiedlog_format, convert_unifiedlog_time_to_datetime, convert_native_time_to_unifiedlog_format
from tests import SysdiagnoseTestCase
import os
import tempfile
import unittest
import json


class TestParsersLogarchive(SysdiagnoseTestCase):

    def test_get_logs_outputdir(self):
        for log_root_path in self.log_root_paths:
            folders = get_log_files(log_root_path)

            with tempfile.TemporaryDirectory() as tmp_outpath:
                print(f'Parsing {folders} to {tmp_outpath}')
                result = parse_path_to_folder(log_root_path, output_folder=tmp_outpath)
                # check if folder is not empty
                self.assertNotEqual(os.listdir(tmp_outpath), [])
                # result should contain at least one entry (linux = stdout, mac = mention it's saved to a file)
                self.assertTrue(result)

                self.assertTrue(os.path.isfile(os.path.join(tmp_outpath, 'logarchive.json')))
                with open(os.path.join(tmp_outpath, 'logarchive.json'), 'r') as f:
                    line = f.readline()
                    json_data = json.loads(line)
                    self.assertTrue('subsystem' in json_data)
                    self.assertTrue('datetime' in json_data)

    def test_get_logs_result(self):
        for log_root_path in self.log_root_paths:
            folders = get_log_files(log_root_path)
            print(f'Parsing {folders}')
            result = parse_path(log_root_path)
            self.assertGreater(len(result), 0)
            self.assertTrue('subsystem' in result[0])
            self.assertTrue('datetime' in result[0])

    def test_convert_native_time_to_unifiedlog(self):
        input = '2023-05-24 13:03:28.908085-0700'
        expected_output = 1684958608908084992
        result = convert_native_time_to_unifiedlog_format(input)
        self.assertEqual(result, expected_output)

        input = '2023-05-24 20:03:28.908085-0000'
        expected_output = 1684958608908084992
        result = convert_native_time_to_unifiedlog_format(input)
        self.assertEqual(result, expected_output)

    def test_convert_unifiedlog_time_to_datetime(self):
        input = 1684958608908085200
        expected_output = '2023-05-24T20:03:28.908085+00:00'
        result = convert_unifiedlog_time_to_datetime(input).isoformat()
        self.assertEqual(result, expected_output)

    def test_convert_entry_to_un(self):
        input = {
            'timezoneName': '',
            'messageType': 'Default',
            'eventType': 'logEvent',
            'source': None,
            'formatString': 'FIPSPOST_KEXT [%llu] %s:%d: PASSED: (%u ms) - fipspost_post_integrity\n',
            'userID': 0,
            'activityIdentifier': 0,
            'subsystem': '',
            'category': '',
            'threadID': 101,
            'senderImageUUID': 'A6F4A2BD-5575-37EB-91C0-28AB00C8FCBF',
            'backtrace': {
                'frames': [
                    {
                        'imageOffset': 6084,
                        'imageUUID': 'A6F4A2BD-5575-37EB-91C0-28AB00C8FCBF'
                    }
                ]
            },
            'bootUUID': '49BA93E4-C511-47A3-B6CC-62D80BFFE539',
            'processImagePath': '/kernel',
            'senderImagePath': '/System/Library/Extensions/corecrypto.kext/corecrypto',
            'timestamp': '2023-05-24 13:03:28.908085-0700',
            'machTimestamp': 161796510,
            'eventMessage': 'FIPSPOST_KEXT [161796151] fipspost_post:169: PASSED: (1 ms) - fipspost_post_integrity',
            'processImageUUID': '39395A83-7379-3C29-AB78-D1B5EDB9C714',
            'traceID': 444438921084932,
            'processID': 0,
            'senderProgramCounter': 6084,
            'parentActivityIdentifier': 0
        }
        expected_output = {
            'timezone_name': '',
            'log_type': 'Default',
            'event_type': 'logEvent',
            'source': None,
            'raw_message': 'FIPSPOST_KEXT [%llu] %s:%d: PASSED: (%u ms) - fipspost_post_integrity\n',
            'euid': 0,
            'activity_id': 0,
            'subsystem': '',
            'category': '',
            'thread_id': 101,
            'library_uuid': 'A6F4A2BD557537EB91C028AB00C8FCBF',
            'backtrace': {'frames': [{'imageOffset': 6084, 'imageUUID': 'A6F4A2BD-5575-37EB-91C0-28AB00C8FCBF'}]},
            'boot_uuid': '49BA93E4C51147A3B6CC62D80BFFE539',
            'process': '/kernel',
            'library': '/System/Library/Extensions/corecrypto.kext/corecrypto',
            'time': 1684958608908084992,
            'machTimestamp': 161796510,
            'message': 'FIPSPOST_KEXT [161796151] fipspost_post:169: PASSED: (1 ms) - fipspost_post_integrity',
            'process_uuid': '39395A8373793C29AB78D1B5EDB9C714',
            'traceID': 444438921084932,
            'pid': 0,
            'senderProgramCounter': 6084,
            'parentActivityIdentifier': 0,
            'datetime': '2023-05-24 13:03:28.908085-0700'
        }
        result = convert_entry_to_unifiedlog_format(input)
        self.assertDictEqual(result, expected_output)


if __name__ == '__main__':
    unittest.main()
