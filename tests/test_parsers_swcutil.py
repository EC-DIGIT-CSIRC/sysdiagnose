from sysdiagnose.parsers.swcutil import SwcutilParser
from tests import SysdiagnoseTestCase
import unittest
import os
from datetime import datetime, timezone


class TestParsersSwcutil(SysdiagnoseTestCase):
    def test_parseswcutil(self):
        for case_id, case in self.sd.cases().items():
            p = SwcutilParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            self.assertGreater(len(result), 0)
            for item in result:
                self.assertTrue('timestamp' in item)

    def test_parse_memory(self):
        p = SwcutilParser(self.sd.config, case_id='test')
        p.sysdiagnose_creation_datetime = datetime.fromtimestamp(1, tz=timezone.utc)
        inputs = [
            'foo:      6 KB',
            'bar: 434 bytes',
            'hello:     10 MB'
        ]
        expected_outputs = [
            {'section': 'memory', 'datetime': '1970-01-01T00:00:01.000000+00:00', 'timestamp': 1.0, 'timestamp_desc': 'Sysdiagnose creation', 'process': 'foo', 'usage': 6144},
            {'section': 'memory', 'datetime': '1970-01-01T00:00:01.000000+00:00', 'timestamp': 1.0, 'timestamp_desc': 'Sysdiagnose creation', 'process': 'bar', 'usage': 434},
            {'section': 'memory', 'datetime': '1970-01-01T00:00:01.000000+00:00', 'timestamp': 1.0, 'timestamp_desc': 'Sysdiagnose creation', 'process': 'hello', 'usage': 10485760}
        ]
        for input, expected_output in zip(inputs, expected_outputs):
            result = p.parse_memory_entry(input)
            self.assertDictEqual(result, expected_output)


if __name__ == '__main__':
    unittest.main()
