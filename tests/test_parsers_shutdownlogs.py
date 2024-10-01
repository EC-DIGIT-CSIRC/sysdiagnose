from sysdiagnose.parsers.shutdownlogs import ShutdownLogsParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersShutdownlogs(SysdiagnoseTestCase):

    def test_parse_shutdownlog(self):
        for case_id, case in self.sd.cases().items():
            p = ShutdownLogsParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            self.assertGreater(len(result), 0)
            for item in result:
                self.assertTrue('pid' in item)
                self.assertTrue('path' in item)


if __name__ == '__main__':
    unittest.main()
