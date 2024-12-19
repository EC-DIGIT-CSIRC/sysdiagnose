from sysdiagnose.parsers.olddsc import OldDscParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersOlddsc(SysdiagnoseTestCase):

    def test_parse_olddsc_file(self):
        for case_id, case in self.sd.cases().items():
            p = OldDscParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            for entry in result:
                self.assertTrue('Load_Address' in entry)
                # self.assertTrue('Unslid_Base_Address' in result)
                # self.assertTrue('Cache_UUID_String' in result)
                # self.assertTrue('Binaries' in result)
                # self.assertTrue(len(result['Binaries']) > 0)


if __name__ == '__main__':
    unittest.main()
