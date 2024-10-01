from sysdiagnose.parsers.lockdownd import LockdowndParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersLockdownd(SysdiagnoseTestCase):

    def test_parse_lockdownd(self):
        for case_id, case in self.sd.cases().items():

            p = LockdowndParser(self.sd.config, case_id=case_id)

            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            first = p.get_result()[0]
            self.assertTrue('timestamp' in first)

    def test_parse_lockdownd_simple(self):
        input = [
            '05/24/23 12:55:38.410307 pid=76 mglog: libMobileGestalt utility.c:70: Could not open /private/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist: No such file or directory',
            '05/24/23 12:55:38.453538 pid=76 data_ark_set_block_invoke: dirtied by changing -HasSiDP',
            '05/24/23 12:55:45.978543 pid=76 lockstart_local: Build version: 19H349'
        ]
        expected_result = [
            {
                'timestamp': 1684932938.410307,
                'datetime': '2023-05-24T12:55:38.410307+00:00',
                'pid': 76,
                'event_type': 'mglog',
                'msg': 'libMobileGestalt utility.c:70: Could not open /private/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist: No such file or directory'
            },
            {
                'timestamp': 1684932938.453538,
                'datetime': '2023-05-24T12:55:38.453538+00:00',
                'pid': 76,
                'event_type': 'data_ark_set_block_invoke',
                'msg': 'dirtied by changing -HasSiDP'
            },
            {
                'timestamp': 1684932945.978543,
                'datetime': '2023-05-24T12:55:45.978543+00:00',
                'pid': 76,
                'event_type': 'lockstart_local',
                'msg': 'Build version: 19H349'
            }
        ]
        result = LockdowndParser.extract_from_list(input)
        self.maxDiff = None
        self.assertEqual(result, expected_result)

    def test_parse_lockdownd_multiline(self):
        input = [
            '05/24/23 12:55:45.978543 pid=76 lockstart_local: Build version: 19H349',
            'hello world',
            '05/24/23 12:55:45.978543 pid=76 lockstart_local: Build version: 19H349'
        ]

        expected_result = [
            {
                'timestamp': 1684932945.978543,
                'datetime': '2023-05-24T12:55:45.978543+00:00',
                'pid': 76,
                'event_type': 'lockstart_local',
                'msg': 'Build version: 19H349hello world'
            },
            {
                'timestamp': 1684932945.978543,
                'datetime': '2023-05-24T12:55:45.978543+00:00',
                'pid': 76,
                'event_type': 'lockstart_local',
                'msg': 'Build version: 19H349'
            }
        ]
        result = LockdowndParser.extract_from_list(input)
        self.maxDiff = None
        self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main()
