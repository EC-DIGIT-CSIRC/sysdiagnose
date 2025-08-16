from sysdiagnose.parsers.spindumpnosymbols import SpindumpNoSymbolsParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersSpindumpnosymbols(SysdiagnoseTestCase):

    def test_parsespindumpNS(self):
        for case_id, case in self.sd.cases().items():
            p = SpindumpNoSymbolsParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            self.assertGreater(len(result), 1)
            self.assertTrue('os_version' in result[0]['data'])
            for item in result:
                self.assert_has_required_fields_jsonl(item)

    def test_parse_basic(self):
        lines = [
            'Date/Time:        2023-05-24 13:29:15.759 -0700',
            'End time:         2023-05-24 13:29:17.757 -0700',
            'OS Version:       iPhone OS 15.7.6 (Build 19H349)',
            'Architecture:     arm64',
            'Report Version:   35.1',
        ]
        expected_result = {
            'datetime': '2023-05-24T13:29:15.759000-07:00',
            'message': 'spindump',
            'data': {
                'end_time': '2023-05-24 13:29:17.757 -0700',
                'os_version': 'iPhone OS 15.7.6 (Build 19H349)',
                'architecture': 'arm64',
                'report_version': '35.1'
            },
            'module': 'spindumpnosymbols',
            'timestamp_desc': 'spindump'
        }
        result = SpindumpNoSymbolsParser.parse_basic(lines)
        self.maxDiff = None
        self.assertDictEqual(expected_result, result)

    def test_parse_basic_nomili(self):
        lines = [
            'Date/Time:        2023-05-24 13:29:15 -0700',
        ]
        expected_result = {
            'datetime': '2023-05-24T13:29:15.000000-07:00',
            'timestamp_desc': 'spindump',
            'module': 'spindumpnosymbols',
            'message': 'spindump',
            'data': {}
        }
        result = SpindumpNoSymbolsParser.parse_basic(lines)
        self.maxDiff = None
        self.assertDictEqual(expected_result, result)

    def test_parse_process(self):
        lines = [
            'Process:          accessoryd [176]',
            'UUID:             BDBDD550-2B15-382C-BB61-1798AFD60460',
            'Path:             /System/Library/PrivateFrameworks/CoreAccessories.framework/Support/accessoryd',
            'Shared Cache:     6D5223AF-7B75-3593-9CC4-5DBD74C56497 slid base address 0x180734000, slide 0x734000',
            'Architecture:     arm64',
            'Parent:           launchd [1]',
            'UID:              501',
            'Sudden Term:      Tracked (allows idle exit)',
            'Footprint:        3792 KB',
            'Time Since Fork:  201s',
            'Num samples:      8 (1-8)',
            'Note:             1 idle work queue thread omitted',
            '  Thread 0x8b6    DispatchQueue "com.apple.main-thread"(1)    8 samples (1-8)    priority 31 (base 31)',
            '  8  ??? (dyld + 99536) [0x102c504d0]',
            '    8  ??? (accessoryd + 554572) [0x10287b64c]',
            '      8  ??? (Foundation + 99872) [0x1821c1620]',
            '        8  ??? (Foundation + 97964) [0x1821c0eac]',
            '          8  ??? (CoreFoundation + 123252) [0x180ab3174]',
            '            8  ??? (CoreFoundation + 44944) [0x180a9ff90]',
            '              8  ??? (CoreFoundation + 27784) [0x180a9bc88]',
            '                8  ??? (libsystem_kernel.dylib + 2732) [0x1bb3f9aac]',
            '                 *8  ??? [0xfffffff0071a86d4]',
            '  Binary Images:',
            '           0x1027f4000 -                ???  accessoryd             <BDBDD550-2B15-382C-BB61-1798AFD60460>  /System/Library/PrivateFrameworks/CoreAccessories.framework/Support/accessoryd',
            '           0x102c38000 -        0x102ca3fff  dyld                   <58AB16CE-D7E0-32D3-946D-4F68FB1A4A17>  /cores/dyld',
            '           0x180a95000 -        0x180ed2fff  CoreFoundation         <717D70C9-3B8E-3ABC-AE16-050588FC3EE8>  /System/Library/Frameworks/CoreFoundation.framework/CoreFoundation',
            '           0x1821a9000 -        0x18248dfff  Foundation             <C3A840E1-0D11-32A3-937F-7F668FFB13F0>  /System/Library/Frameworks/Foundation.framework/Foundation',
            '           0x1bb3f9000 -        0x1bb42cfff  libsystem_kernel.dylib <D3BAC787-09EE-3319-BE24-4115817391E2>  /usr/lib/system/libsystem_kernel.dylib',

        ]
        expected_result = {
            'process': 'accessoryd',
            'pid': 176,
            'ppid': 1,
            'uuid': 'BDBDD550-2B15-382C-BB61-1798AFD60460',
            'path': '/System/Library/PrivateFrameworks/CoreAccessories.framework/Support/accessoryd',
            'shared_cache': '6D5223AF-7B75-3593-9CC4-5DBD74C56497 slid base address 0x180734000, slide 0x734000',
            'architecture': 'arm64',
            'parent': 'launchd',
            'uid': 501,
            'sudden_term': 'Tracked (allows idle exit)',
            'footprint': '3792 KB',
            'time_since_fork': '201s',
            'num_samples': '8 (1-8)',
            'note': '1 idle work queue thread omitted',
            'threads': [
                {
                    'thread': '0x8b', 'dispatch_queue': 'com.apple.main-thread', 'priority': '31',
                    'loaded':
                        [{'library': 'dyld', 'int': '99536', 'hex': '0x102c504d0'}, {'library': 'accessoryd', 'int': '554572', 'hex': '0x10287b64c'}, {'library': 'Foundation', 'int': '99872', 'hex': '0x1821c1620'}, {'library': 'Foundation', 'int': '97964', 'hex': '0x1821c0eac'}, {'library': 'CoreFoundation', 'int': '123252', 'hex': '0x180ab3174'}, {'library': 'CoreFoundation', 'int': '44944', 'hex': '0x180a9ff90'}, {'library': 'CoreFoundation', 'int': '27784', 'hex': '0x180a9bc88'}, {'library': 'libsystem_kernel.dylib', 'int': '2732', 'hex': '0x1bb3f9aac'}, {'hex': '0xfffffff0071a86d4'}]
                }],
            'images': [
                {'start': '0x1027f4000', 'end': '???', 'image': 'accessoryd', 'uuid': 'BDBDD550-2B15-382C-BB61-1798AFD60460', 'path': '/System/Library/PrivateFrameworks/CoreAccessories.framework/Support/accessoryd'},
                {'start': '0x102c38000', 'end': '0x102ca3fff', 'image': 'dyld', 'uuid': '58AB16CE-D7E0-32D3-946D-4F68FB1A4A17', 'path': '/cores/dyld'},
                {'start': '0x180a95000', 'end': '0x180ed2fff', 'image': 'CoreFoundation', 'uuid': '717D70C9-3B8E-3ABC-AE16-050588FC3EE8', 'path': '/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation'},
                {'start': '0x1821a9000', 'end': '0x18248dfff', 'image': 'Foundation', 'uuid': 'C3A840E1-0D11-32A3-937F-7F668FFB13F0', 'path': '/System/Library/Frameworks/Foundation.framework/Foundation'},
                {'start': '0x1bb3f9000', 'end': '0x1bb42cfff', 'image': 'libsystem_kernel.dylib', 'uuid': 'D3BAC787-09EE-3319-BE24-4115817391E2', 'path': '/usr/lib/system/libsystem_kernel.dylib'}
            ]
        }
        result = SpindumpNoSymbolsParser.parse_process(lines)
        self.maxDiff = None
        self.assertDictEqual(expected_result, result)

    def test_parse_thread(self):
        self.maxDiff = None

        lines = [
            'Thread 0x8b6    DispatchQueue "com.apple.main-thread"(1)    8 samples (1-8)    priority 31 (base 31)',
            '  8  ??? (dyld + 99536) [0x102c504d0]',
            '    8  ??? (accessoryd + 554572) [0x10287b64c]',
            '      8  ??? (Foundation + 99872) [0x1821c1620]',
            '        8  ??? (Foundation + 97964) [0x1821c0eac]',
            '          8  ??? (CoreFoundation + 123252) [0x180ab3174]',
            '            8  ??? (CoreFoundation + 44944) [0x180a9ff90]',
            '              8  ??? (CoreFoundation + 27784) [0x180a9bc88]',
            '                8  ??? (libsystem_kernel.dylib + 2732) [0x1bb3f9aac]',
            '                 *8  ??? [0xfffffff0071a86d4]'
        ]
        expected_result = {
            'thread': '0x8b', 'dispatch_queue': 'com.apple.main-thread', 'priority': '31',
            'loaded': [
                {'library': 'dyld', 'int': '99536', 'hex': '0x102c504d0'},
                {'library': 'accessoryd', 'int': '554572', 'hex': '0x10287b64c'},
                {'library': 'Foundation', 'int': '99872', 'hex': '0x1821c1620'},
                {'library': 'Foundation', 'int': '97964', 'hex': '0x1821c0eac'},
                {'library': 'CoreFoundation', 'int': '123252', 'hex': '0x180ab3174'},
                {'library': 'CoreFoundation', 'int': '44944', 'hex': '0x180a9ff90'},
                {'library': 'CoreFoundation', 'int': '27784', 'hex': '0x180a9bc88'},
                {'library': 'libsystem_kernel.dylib', 'int': '2732', 'hex': '0x1bb3f9aac'},
                {'hex': '0xfffffff0071a86d4'}
            ]}
        result = SpindumpNoSymbolsParser.parse_thread(lines)
        self.assertDictEqual(expected_result, result)

        lines = [
            'Thread 0x62d    DispatchQueue "com.apple.main-thread"(1)    8 samples (1-8)    priority 31 (base 31)    cpu time 0.005s (4.2M cycles, 1986.9K instructions, 2.14c/i)',
            '  8  ??? (dyld + 99536) [0x10236c4d0]',
            '    8  ??? (apsd + 281160) [0x10205ca48]'
        ]
        expected_result = {
            'thread': '0x62', 'dispatch_queue': 'com.apple.main-thread', 'priority': '31', 'cputime': '0.005s (4.2M cycles, 1986.9K instructions, 2.14c/i)',
            'loaded': [
                {'library': 'dyld', 'int': '99536', 'hex': '0x10236c4d0'},
                {'library': 'apsd', 'int': '281160', 'hex': '0x10205ca48'}
            ]
        }
        result = SpindumpNoSymbolsParser.parse_thread(lines)
        self.assertDictEqual(expected_result, result)

        lines = [
            'Thread 0x8477d    Thread name "IOConfigThread_\'foobar\'"    1 sample (295)    priority 80 (base 80)    cpu time <0.001s',
            '*1  ??? (kernel + 850132) [0xffffff80002df8d4] (running)'
        ]
        expected_result = {
            'thread': '0x84', 'thread_name': "IOConfigThread_'foobar'", 'priority': '80', 'cputime': '<0.001s',
            'loaded': [
                {'library': 'kernel', 'int': '850132', 'hex': '0xffffff80002df8d4', 'status': 'running'}
            ]
        }
        result = SpindumpNoSymbolsParser.parse_thread(lines)
        self.assertDictEqual(expected_result, result)


if __name__ == '__main__':
    unittest.main()
