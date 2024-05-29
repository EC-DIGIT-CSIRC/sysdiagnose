from parsers.ps import parse_path, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersPs(SysdiagnoseTestCase):

    def test_parse_ps(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            self.assertTrue(len(files) > 0)
            for file in files:
                print(f'Parsing {file}')
                result = parse_path(file)
                if result:  # not all logs contain data
                    for item in result.values():
                        self.assertTrue('COMMAND' in item)
                        self.assertTrue('PID' in item)
                        self.assertTrue('USER' in item)


if __name__ == '__main__':
    unittest.main()
