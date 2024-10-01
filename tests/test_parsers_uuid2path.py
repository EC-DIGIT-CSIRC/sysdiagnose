from tests import SysdiagnoseTestCase
from sysdiagnose.parsers.uuid2path import UUID2PathParser
import unittest
import os


class TestParsersUuid2path(SysdiagnoseTestCase):
    def test_uuid2path(self):
        for case_id, case in self.sd.cases().items():
            p = UUID2PathParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            if not files:
                continue

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            self.assertGreater(len(result), 0)


if __name__ == '__main__':
    unittest.main()
