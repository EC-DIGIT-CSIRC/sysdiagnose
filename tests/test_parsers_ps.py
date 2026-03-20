from sysdiagnose.parsers.ps import PsParser
from tests import SysdiagnoseTestCase
import unittest
import tempfile
import os
from datetime import datetime, timezone


class TestParsersPs(SysdiagnoseTestCase):

    def test_parse_ps(self):
        for case_id, case in self.sd.cases().items():

            p = PsParser(self.sd.config, case_id=case_id)

            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            if p.get_result():  # not all logs contain data
                for item in p.get_result():
                    # Test original fields still exist
                    self.assertTrue('command' in item['data'])
                    self.assertTrue('pid' in item['data'])
                    self.assertTrue('user' in item['data'])

                    # Test new enhanced fields exist
                    self.assertTrue('process_name' in item['data'])
                    self.assertIn('process_args', item['data'])  # Can be None
                    self.assertIn('parent_process', item['data'])  # Can be None
                    self.assertTrue('process_name_resolved' in item['data'])

                    self.assert_has_required_fields_jsonl(item)

    def test_parse_ps_lower_than_v16(self):
        input = [
            'USER             UID   PID  PPID  %CPU %MEM PRI NI      VSZ    RSS WCHAN    TT  STAT STARTED      TIME COMMAND',
            'root               0     1     0   0.0  0.4  37  0  4226848   8912 -        ??  Ss   14Jan19   7:27.40 /sbin/launchd with space'
        ]
        expected_result = [
            {
                'data': {
                    'user': 'root',
                    'owner_user_id': 0,  # standardized from 'uid'
                    'pid': 1,
                    'ppid': 0,
                    'cpu_usage_percent': 0.0,  # standardized from '%cpu' -> 'cpu'
                    'memory_usage_percent': 0.4,  # standardized from '%mem' -> 'mem'
                    'kernel_priority': 37,  # standardized from 'pri'
                    'nice_priority_adjustment': 0,  # standardized from 'ni'
                    'vsz': 4226848,  # no mapping, keeps original
                    'physical_memory_kb': 8912,  # standardized from 'rss'
                    'wchan': '-',  # no mapping, keeps original
                    'tt': '??',  # no mapping, keeps original
                    'stat': 'Ss',  # no mapping, keeps original
                    'started': '14Jan19',  # no mapping, keeps original
                    'time': '7:27.40',  # no mapping, keeps original
                    'command': '/sbin/launchd with space',

                    # New enhanced fields
                    'process_name': '/sbin/launchd',
                    'process_args': 'with space',
                    'parent_process': None,  # ppid=0, no parent found
                    'process_name_resolved': False,  # not heuristically resolved

                    'timestamp_info': 'sysdiagnose creation time'
                },
                'datetime': '1970-01-01T00:00:01.000000+00:00',
                'module': 'ps',
                'message': 'Process /sbin/launchd with space [1] running as root',
                'timestamp_desc': 'process running'
            }
        ]
        tmp_inputfile = tempfile.NamedTemporaryFile()
        with open(tmp_inputfile.name, 'w') as f:
            f.write('\n'.join(input))
        p = PsParser(self.sd.config, case_id='test')
        p.sysdiagnose_creation_datetime = datetime.fromtimestamp(1, tz=timezone.utc)
        result = p.parse_file(tmp_inputfile.name)
        tmp_inputfile.close()
        self.maxDiff = None
        self.assertEqual(result, expected_result)

    def test_parse_ps_newer_than_v16(self):
        input = [
            'USER  UID PRSNA   PID  PPID        F  %CPU %MEM PRI NI      VSZ    RSS WCHAN    TT  STAT STARTED      TIME COMMAND',
            'root  0     -     1     0     4004   0.0  0.0   0  0        0      0 -        ??  ?s   Tue09PM   0:00.00 /sbin/launchd'
        ]
        expected_result = [
            {
                'data': {
                    'user': 'root',
                    'owner_user_id': 0,  # standardized from 'uid'
                    'process_resident_address': '-',  # standardized from 'prsna'
                    'pid': 1,
                    'ppid': 0,
                    'process_flags_bitmask': 4004,  # standardized from 'f'
                    'cpu_usage_percent': 0.0,  # standardized from '%cpu' -> 'cpu'
                    'memory_usage_percent': 0.0,  # standardized from '%mem' -> 'mem'
                    'kernel_priority': 0,  # standardized from 'pri'
                    'nice_priority_adjustment': 0,  # standardized from 'ni'
                    'virtual_memory_kb': 0,  # standardized from 'vsz'
                    'physical_memory_kb': 0,  # standardized from 'rss'
                    'kernel_wait_channel': '-',  # standardized from 'wchan'
                    'controlling_terminal': '??',  # standardized from 'tt'
                    'stat': '?s',  # no mapping, keeps original
                    'started': 'Tue09PM',  # no mapping, keeps original
                    'time': '0:00.00',  # no mapping, keeps original
                    'command': '/sbin/launchd',

                    # New enhanced fields
                    'process_name': '/sbin/launchd',
                    'process_args': None,  # no arguments
                    'parent_process': None,  # ppid=0, no parent found
                    'process_name_resolved': False,  # not heuristically resolved

                    'timestamp_info': 'sysdiagnose creation time'
                },
                'datetime': '1970-01-01T00:00:01.000000+00:00',
                'module': 'ps',
                'message': 'Process /sbin/launchd [1] running as root',
                'timestamp_desc': 'process running'
            }
        ]
        tmp_inputfile = tempfile.NamedTemporaryFile()
        with open(tmp_inputfile.name, 'w') as f:
            f.write('\n'.join(input))
        p = PsParser(self.sd.config, case_id='test')
        p.sysdiagnose_creation_datetime = datetime.fromtimestamp(1, tz=timezone.utc)
        result = p.parse_file(tmp_inputfile.name)
        tmp_inputfile.close()
        self.assertEqual(result, expected_result)

    def test_ps_exclude_known_goods(self):
        processes = [
            {'command': 'good', 'pid': 1},
            {'command': 'bad', 'pid': 2},
            {'command': 'unknown', 'pid': 3}
        ]
        known_good = [
            {'command': 'good', 'pid': 1}
        ]
        expected_result = [
            {'command': 'bad', 'pid': 2},
            {'command': 'unknown', 'pid': 3}
        ]
        result = PsParser.exclude_known_goods(processes, known_good)
        self.assertEqual(result, expected_result)

    def test_process_name_resolution(self):
        """Test heuristic process name resolution"""
        input = [
            'USER  UID   PID  PPID  %CPU %MEM COMMAND',
            'root    0     1     0   0.0  0.1 sshd: user@pts/0',
            'www     1     2     1   0.1  0.2 /usr/bin/httpd -D FOREGROUND'
        ]

        tmp_inputfile = tempfile.NamedTemporaryFile()
        with open(tmp_inputfile.name, 'w') as f:
            f.write('\n'.join(input))

        p = PsParser(self.sd.config, case_id='test')
        p.sysdiagnose_creation_datetime = datetime.fromtimestamp(1, tz=timezone.utc)
        result = p.parse_file(tmp_inputfile.name)
        tmp_inputfile.close()

        # Check first process (sshd with heuristic resolution)
        sshd_process = result[0]['data']
        self.assertEqual(sshd_process['process_name'], '/usr/sbin/sshd')  # resolved
        self.assertEqual(sshd_process['process_args'], 'user@pts/0')
        self.assertTrue(sshd_process['process_name_resolved'])  # was resolved heuristically
        self.assertEqual(sshd_process['parent_process'], None)  # ppid=0

        # Check second process (normal process)
        httpd_process = result[1]['data']
        self.assertEqual(httpd_process['process_name'], '/usr/bin/httpd')  # not resolved
        self.assertEqual(httpd_process['process_args'], '-D FOREGROUND')
        self.assertFalse(httpd_process['process_name_resolved'])  # was not resolved
        self.assertEqual(httpd_process['parent_process'], '/usr/sbin/sshd')  # resolved parent


if __name__ == '__main__':
    unittest.main()
