from parsers.ps import PsParser
from tests import SysdiagnoseTestCase
import unittest
import tempfile
import os


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
                    self.assertTrue('COMMAND' in item)
                    self.assertTrue('PID' in item)
                    self.assertTrue('USER' in item)

    def test_parse_ps_lower_than_v16(self):
        input = [
            'USER             UID   PID  PPID  %CPU %MEM PRI NI      VSZ    RSS WCHAN    TT  STAT STARTED      TIME COMMAND',
            'root               0     1     0   0.0  0.4  37  0  4226848   8912 -        ??  Ss   14Jan19   7:27.40 /sbin/launchd with space'
        ]
        expected_result = [
            {'USER': 'root', 'UID': 0, 'PID': 1, 'PPID': 0, '%CPU': 0.0, '%MEM': 0.4, 'PRI': 37, 'NI': 0, 'VSZ': 4226848, 'RSS': 8912, 'WCHAN': '-', 'TT': '??', 'STAT': 'Ss', 'STARTED': '14Jan19', 'TIME': '7:27.40', 'COMMAND': '/sbin/launchd with space'}
        ]
        tmp_inputfile = tempfile.NamedTemporaryFile()
        with open(tmp_inputfile.name, 'w') as f:
            f.write('\n'.join(input))
        result = PsParser.parse_file(tmp_inputfile.name)
        tmp_inputfile.close()
        self.assertEqual(result, expected_result)

    def test_parse_ps_newer_than_v16(self):
        input = [
            'USER  UID PRSNA   PID  PPID        F  %CPU %MEM PRI NI      VSZ    RSS WCHAN    TT  STAT STARTED      TIME COMMAND',
            'root  0     -     1     0     4004   0.0  0.0   0  0        0      0 -        ??  ?s   Tue09PM   0:00.00 /sbin/launchd'
        ]
        expected_result = [
            {'USER': 'root', 'UID': 0, 'PRSNA': '-', 'PID': 1, 'PPID': 0, 'F': 4004, '%CPU': 0.0, '%MEM': 0.0, 'PRI': 0, 'NI': 0, 'VSZ': 0, 'RSS': 0, 'WCHAN': '-', 'TT': '??', 'STAT': '?s', 'STARTED': 'Tue09PM', 'TIME': '0:00.00', 'COMMAND': '/sbin/launchd'}
        ]
        tmp_inputfile = tempfile.NamedTemporaryFile()
        with open(tmp_inputfile.name, 'w') as f:
            f.write('\n'.join(input))
        result = PsParser.parse_file(tmp_inputfile.name)
        tmp_inputfile.close()
        self.assertEqual(result, expected_result)

    def test_ps_exclude_known_goods(self):
        processes = [
            {'COMMAND': 'good', 'PID': 1},
            {'COMMAND': 'bad', 'PID': 2},
            {'COMMAND': 'unknown', 'PID': 3}
        ]
        known_good = [
            {'COMMAND': 'good', 'PID': 1}
        ]
        expected_result = [
            {'COMMAND': 'bad', 'PID': 2},
            {'COMMAND': 'unknown', 'PID': 3}
        ]
        result = PsParser.exclude_known_goods(processes, known_good)
        self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main()
