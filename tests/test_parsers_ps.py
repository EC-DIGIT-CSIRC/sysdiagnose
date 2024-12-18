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
                    self.assertTrue('command' in item)
                    self.assertTrue('pid' in item)
                    self.assertTrue('user' in item)

    def test_parse_ps_lower_than_v16(self):
        input = [
            'USER             UID   PID  PPID  %CPU %MEM PRI NI      VSZ    RSS WCHAN    TT  STAT STARTED      TIME COMMAND',
            'root               0     1     0   0.0  0.4  37  0  4226848   8912 -        ??  Ss   14Jan19   7:27.40 /sbin/launchd with space'
        ]
        expected_result = [
            {
                'user': 'root', 'uid': 0, 'pid': 1, 'ppid': 0, '%cpu': 0.0, '%mem': 0.4, 'pri': 37, 'ni': 0, 'vsz': 4226848, 'rss': 8912, 'wchan': '-', 'tt': '??', 'stat': 'Ss', 'started': '14Jan19', 'time': '7:27.40', 'command': '/sbin/launchd with space',
                'timestamp_desc': 'sysdiagnose creation',
                'timestamp': 1.0,
                'datetime': '1970-01-01T00:00:01.000000+00:00'
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

    def test_parse_ps_newer_than_v16(self):
        input = [
            'USER  UID PRSNA   PID  PPID        F  %CPU %MEM PRI NI      VSZ    RSS WCHAN    TT  STAT STARTED      TIME COMMAND',
            'root  0     -     1     0     4004   0.0  0.0   0  0        0      0 -        ??  ?s   Tue09PM   0:00.00 /sbin/launchd'
        ]
        expected_result = [
            {
                'user': 'root', 'uid': 0, 'prsna': '-', 'pid': 1, 'ppid': 0, 'f': 4004, '%cpu': 0.0, '%mem': 0.0, 'pri': 0, 'ni': 0, 'vsz': 0, 'rss': 0, 'wchan': '-', 'tt': '??', 'stat': '?s', 'started': 'Tue09PM', 'time': '0:00.00', 'command': '/sbin/launchd',
                'timestamp_desc': 'sysdiagnose creation',
                'timestamp': 1.0,
                'datetime': '1970-01-01T00:00:01.000000+00:00'
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


if __name__ == '__main__':
    unittest.main()
