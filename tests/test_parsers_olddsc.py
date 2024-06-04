from parsers.olddsc import parse_path, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersOlddsc(SysdiagnoseTestCase):

    def test_parse_olddsc_file(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            print(f'Parsing {files}')
            result = parse_path(log_root_path)
            self.assertTrue('Unslid_Base_Address' in result)
            self.assertTrue('Cache_UUID_String' in result)
            self.assertTrue('Binaries' in result)
            self.assertTrue(len(result['Binaries']) > 0)


if __name__ == '__main__':
    unittest.main()
