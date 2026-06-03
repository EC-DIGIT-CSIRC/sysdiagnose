import os
import unittest
from datetime import UTC, datetime

from sysdiagnose.parsers.swcutil import SwcutilParser
from tests import SysdiagnoseTestCase


class TestParsersSwcutil(SysdiagnoseTestCase):
    def test_parseswcutil(self):
        for case_id, _case in self.sd.cases().items():
            p = SwcutilParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            if not files:
                self.skipTest("No swcutil_show.txt file present")

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            self.assertGreater(len(result), 0)
            for item in result:
                self.assert_has_required_fields_jsonl(item)
            self.assert_result_summary_consistent(p, result)

    def test_parse_memory(self):
        p = SwcutilParser(self.sd.config, case_id='test')
        p.sysdiagnose_creation_datetime = datetime.fromtimestamp(1, tz=UTC)
        inputs = [
            'foo:      6 KB',
            'bar: 434 bytes',
            'hello:     10 MB'
        ]
        expected_outputs = [
            {'module': 'swcutil', 'datetime': '1970-01-01T00:00:01.000000+00:00', 'timestamp_desc': 'memory usage at sysdiagnose creation', 'data': {'section': 'memory', 'process': 'foo', 'usage': 6144}, 'message': 'foo memory usage: 6144 bytes'},
            {'module': 'swcutil', 'datetime': '1970-01-01T00:00:01.000000+00:00', 'timestamp_desc': 'memory usage at sysdiagnose creation', 'data': {'section': 'memory', 'process': 'bar', 'usage': 434}, 'message': 'bar memory usage: 434 bytes'},
            {'module': 'swcutil', 'datetime': '1970-01-01T00:00:01.000000+00:00', 'timestamp_desc': 'memory usage at sysdiagnose creation', 'data': {'section': 'memory', 'process': 'hello', 'usage': 10485760}, 'message': 'hello memory usage: 10485760 bytes'}
        ]
        for input, expected_output in zip(inputs, expected_outputs, strict=False):
            result = p.parse_memory_entry(input)
            self.assertDictEqual(result, expected_output)


if __name__ == '__main__':
    unittest.main()
