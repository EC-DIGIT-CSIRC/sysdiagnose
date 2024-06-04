from parsers.swcutil import parse_path, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersSwcutil(SysdiagnoseTestCase):
    def test_parseswcutil(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            self.assertTrue(len(files) > 0)
            print(f'Parsing {files}')
            result = parse_path(log_root_path)
            self.assertGreater(len(result), 0)
            self.assertTrue('headers' in result)
            self.assertTrue('network' in result)
            self.assertTrue('headers' in result)

            self.assertGreater(len(result['memory']), 0)
            self.assertGreater(len(result['db']), 0)


if __name__ == '__main__':
    unittest.main()
