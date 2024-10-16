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


if __name__ == '__main__':
    unittest.main()
