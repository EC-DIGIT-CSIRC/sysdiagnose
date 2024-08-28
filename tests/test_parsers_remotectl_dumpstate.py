from parsers.remotectl_dumpstate import RemotectlDumpstateParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersRemotectlDumpstate(SysdiagnoseTestCase):

    def test_get_remotectldumpstate(self):
        for case_id, case in self.sd.cases().items():
            p = RemotectlDumpstateParser(self.sd.config, case_id=case_id)

            files = p.get_log_files()
            self.assertEqual(len(files), 1)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            if result:
                self.assertTrue('Local device' in result)


if __name__ == '__main__':
    unittest.main()
