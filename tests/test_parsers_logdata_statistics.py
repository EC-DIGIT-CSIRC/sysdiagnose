from sysdiagnose.parsers.logdata_statistics import LogDataStatisticsParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersLogdataStatistics(SysdiagnoseTestCase):

    def test_logdatastatisticstxt(self):
        for case_id, case in self.sd.cases().items():
            p = LogDataStatisticsParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            if not files:  # we may not have backup
                continue

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            for item in result:
                self.assertTrue('process' in item)
                self.assert_has_required_fields_jsonl(item)


if __name__ == '__main__':
    unittest.main()
