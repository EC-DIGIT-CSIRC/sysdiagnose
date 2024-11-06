from sysdiagnose.parsers.crashlogs import CrashLogsParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersCrashlogs(SysdiagnoseTestCase):

    def test_parse_crashlogs(self):
        for case_id, case in self.sd.cases().items():
            p = CrashLogsParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            for item in result:
                self.assertTrue('timestamp' in item)

    def test_header_section(self):
        lines = [
            'Date/Time:        2024-08-30 11:18:54.620 +0200',
            'End time:         2024-08-30 11:21:00.954 +0200',
            'OS Version:       iPhone OS 17.6.1 (Build 21G93)',
            'Architecture:     arm64e'
        ]
        expected_results = {'Date/Time': '2024-08-30 11:18:54.620 +0200', 'End time': '2024-08-30 11:21:00.954 +0200', 'OS Version': 'iPhone OS 17.6.1 (Build 21G93)', 'Architecture': 'arm64e'}
        result = CrashLogsParser.process_ips_lines(lines)
        self.maxDiff = None
        self.assertEqual(result, expected_results)

    def test_split_thread(self):
        lines = [
            '0   libsystem_kernel.dylib        	0x0000000123456789 0x123456000 + 123456'
        ]
        expected_results = [
            {'id': '0', 'image_name': 'libsystem_kernel.dylib', 'image_base': '0x0000000123456789', 'image_offset': '0x123456000', 'symbol_offset': '123456'}
        ]
        for line, expected_result in zip(lines, expected_results, strict=True):
            result = CrashLogsParser.split_thread(line)
            self.assertEqual(result, expected_result)

    def test_split_binary_images(self):
        lines = [
            '           0x123456000 -                ???  com.apple.foo (1) <5BFC3EC3-2045-4F95-880A-DEC88832F639>  /System/Library/bar',
            '           0x123456000 -        0x123456fff  libhello                  <5BFC3EC3-2045-4F95-880A-DEC88832F639>  /usr/lib/hello',
            '0x123456000 - 0x123456fff FooBar arm64  <5BFC3EC320454F95880ADEC88832F639> /System/Library/bar',
            '0x123456000 -                ???  ???                                     <5BFC3EC3-2045-4F95-880A-DEC88832F639>',
        ]
        expected_results = [
            {'image_offset_start': '0x123456000', 'image_offset_end': '???',
             'image_name': 'com.apple.foo (1)',
             'uuid': '5BFC3EC3-2045-4F95-880A-DEC88832F639',
             'path': '/System/Library/bar'},
            {'image_offset_start': '0x123456000', 'image_offset_end': '0x123456fff',
             'image_name': 'libhello',
             'uuid': '5BFC3EC3-2045-4F95-880A-DEC88832F639', 'path': '/usr/lib/hello'},
            {'image_offset_start': '0x123456000', 'image_offset_end': '0x123456fff',
             'image_name': 'FooBar arm64',
             'uuid': '5BFC3EC320454F95880ADEC88832F639',
             'path': '/System/Library/bar'},
            {'image_offset_start': '0x123456000', 'image_offset_end': '???',
             'image_name': '???',
             'uuid': '5BFC3EC3-2045-4F95-880A-DEC88832F639', 'path': ''}
        ]
        for line, expected_result in zip(lines, expected_results, strict=True):
            result = CrashLogsParser.split_binary_images(line)
            self.assertEqual(result, expected_result)

    def test_split_thread_crashes_with_arm_thread_state(self):
        lines = [
            '    x0: 0x0000000000000012   x1: 0x0000000000000002   x2: 0x0000000123456789   x3: 0x0000000000000001',
            '   x28: 0x0000000000180000   fp: 0x0000000123456789   lr: 0x0000000123456789',
            '    sp: 0x0000000123456789   pc: 0x0000000123456789 cpsr: 0x40000000',
            '   esr: 0x12345667  Address size fault',
        ]
        expected_results = [
            {'x0': '0x0000000000000012', 'x1': '0x0000000000000002', 'x2': '0x0000000123456789', 'x3': '0x0000000000000001'},
            {'x28': '0x0000000000180000', 'fp': '0x0000000123456789', 'lr': '0x0000000123456789'},
            {'sp': '0x0000000123456789', 'pc': '0x0000000123456789', 'cpsr': '0x40000000'},
            {'esr': '0x12345667', 'error': 'Address size fault'},
        ]
        for line, expected_result in zip(lines, expected_results, strict=True):
            result = CrashLogsParser.split_thread_crashes_with_arm_thread_state(line)
            self.assertEqual(result, expected_result)

    def test_process_ips_lines_json(self):
        lines = [
            '{"foo": "bar"}'
        ]
        expected_results = {"foo": "bar"}
        result = CrashLogsParser.process_ips_lines(lines)
        self.assertEqual(result, expected_results)

    def test_process_ips_lines_plist(self):
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">',
            '<plist version="1.0">',
            '<dict>',
            '	<key>foo</key>',
            '	<string>bar</string>',
            '</dict>',
            '</plist>'
        ]
        expected_results = {"foo": "bar"}
        result = CrashLogsParser.process_ips_lines(lines)
        self.assertEqual(result, expected_results)

    def test_process_ips_lines_text(self):
        lines = [
            'foo: bar'
        ]
        expected_results = {"foo": "bar"}
        result = CrashLogsParser.process_ips_lines(lines)
        self.assertEqual(result, expected_results)


if __name__ == '__main__':
    unittest.main()
