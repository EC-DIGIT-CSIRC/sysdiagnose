from parsers.brctl import BrctlParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersBrctl(SysdiagnoseTestCase):

    def test_parsebrctl(self):
        for case_id, case in self.sd.cases().items():
            p = BrctlParser(self.sd.config, case_id=case_id)
            folders = p.get_log_files()
            self.assertEqual(len(folders), 1)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            print(f'Parsing {folders}')
            result = p.get_result()
            if result:
                self.assertTrue('containers' in result)
                self.assertTrue('boot_history' in result)
                self.assertTrue('server_state' in result)
                self.assertTrue('client_state' in result)
                self.assertTrue('system' in result)
                self.assertTrue('scheduler' in result)
                self.assertTrue('applibrary' in result)
                self.assertTrue('app_library_id' in result)
                self.assertTrue('app_ids' in result)


if __name__ == '__main__':
    unittest.main()
