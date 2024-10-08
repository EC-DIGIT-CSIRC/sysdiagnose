from sysdiagnose.parsers.logarchive import LogarchiveParser
from tests import SysdiagnoseTestCase
import os
import unittest
import json
import tempfile


class TestParsersLogarchive(SysdiagnoseTestCase):

    def test_parse_logarchive(self):
        for case_id, case in self.sd.cases().items():
            print(f'Parsing logarchive for {case_id}')
            p = LogarchiveParser(self.sd.config, case_id=case_id)

            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            # we don't test getting result in memory, but check one line in the output.
            with open(p.output_file, 'r') as f:
                line = f.readline()
                json_data = json.loads(line)
                self.assertTrue('subsystem' in json_data)
                self.assertTrue('datetime' in json_data)

    def test_convert_native_time_to_unifiedlog(self):
        input = '2023-05-24 13:03:28.908085-0700'
        expected_output = 1684958608908084992
        result = LogarchiveParser.convert_native_time_to_unifiedlog_format(input)
        self.assertEqual(result, expected_output)

        input = '2023-05-24 20:03:28.908085-0000'
        expected_output = 1684958608908084992
        result = LogarchiveParser.convert_native_time_to_unifiedlog_format(input)
        self.assertEqual(result, expected_output)

    def test_convert_unifiedlog_time_to_datetime(self):
        input = 1684958608908085200
        expected_output = '2023-05-24T20:03:28.908085+00:00'
        result = LogarchiveParser.convert_unifiedlog_time_to_datetime(input).isoformat(timespec='microseconds')
        self.assertEqual(result, expected_output)

    def test_convert_entry_to_unified(self):
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
            'datetime': '2023-05-24T13:03:28.908085-07:00',
            'timestamp': 1684958608.908085
        }
        result = LogarchiveParser.convert_entry_to_unifiedlog_format(input)
        self.maxDiff = None
        self.assertDictEqual(result, expected_output)

    def test_merge_files(self):
        input = []
        input.append([
            {'time': 1, 'data': 'a'},
            {'time': 2, 'data': 'b'},
            {'time': 3, 'data': 'c'},
            {'time': 4, 'data': 'd'},
            {'time': 5, 'data': 'e'},
            {'time': 6, 'data': 'f'},
            {'time': 7, 'data': 'g'},
        ])
        input.append([
            {'time': 1, 'data': 'a-wrong'},
            {'time': 2, 'data': 'b-wrong'},
            {'time': 3, 'data': 'c-wrong'},
            {'time': 4, 'data': 'd-wrong'},
            {'time': 5, 'data': 'e-wrong'},
            {'time': 6, 'data': 'f-wrong'},
            {'time': 7, 'data': 'g-wrong'},
        ])

        input.append([   # should be ignored
            {'time': 4, 'data': 'd-wrong'},
            {'time': 5, 'data': 'e-wrong'},
            {'time': 6, 'data': 'f-wrong'},
        ])
        input.append([  # overlaps first list, so must be taken from the end of first list
            {'time': 7, 'data': 'g-wrong'},
            {'time': 8, 'data': 'h'},
            {'time': 9, 'data': 'i'},
            {'time': 10, 'data': 'j'},
        ])
        input.append([  # small gap
            {'time': 12, 'data': 'k'},
            {'time': 13, 'data': 'l'},
            {'time': 14, 'data': 'm'},
        ])

        expected_output = [{'time': 1, 'data': 'a'}, {'time': 2, 'data': 'b'}, {'time': 3, 'data': 'c'}, {'time': 4, 'data': 'd'}, {'time': 5, 'data': 'e'}, {'time': 6, 'data': 'f'}, {'time': 7, 'data': 'g'}, {'time': 8, 'data': 'h'}, {'time': 9, 'data': 'i'}, {'time': 10, 'data': 'j'}, {'time': 12, 'data': 'k'}, {'time': 13, 'data': 'l'}, {'time': 14, 'data': 'm'}]

        temp_files = []
        try:
            # write the files with the test data
            for file in input:
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                temp_files.append({
                    'file': temp_file,
                })
                for entry in file:
                    temp_file.write(json.dumps(entry).encode())
                    temp_file.write(b'\n')
                temp_file.close()
            # merge the files
            output_file = tempfile.NamedTemporaryFile(delete=False)
            output_file.close()
            LogarchiveParser.merge_files(temp_files, output_file.name)

            # read the output file
            result = []
            with open(output_file.name, 'r') as f:
                for line in f:
                    result.append(json.loads(line))

        finally:
            for temp_file in temp_files:
                os.remove(temp_file['file'].name)
            os.remove(output_file.name)

        self.assertListEqual(result, expected_output)


if __name__ == '__main__':
    unittest.main()
