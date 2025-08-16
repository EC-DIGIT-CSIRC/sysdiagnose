from sysdiagnose.parsers.containermanager import ContainerManagerParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersContainermanager(SysdiagnoseTestCase):

    def test_parsecontainermanager(self):
        for case_id, case in self.sd.cases().items():
            p = ContainerManagerParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            if len(files) == 0:  # not all seem to have the containermanager
                continue

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            for item in result:
                self.assertTrue('hexID' in item['data'])
                self.assertTrue('loglevel' in item['data'])
                self.assert_has_required_fields_jsonl(item)


if __name__ == '__main__':
    unittest.main()
