from parsers.powerlogs import get_powerlogs, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersPowerlogs(SysdiagnoseTestCase):

    def test_get_powerlogs(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            for file in files:
                print(f'Parsing {file}')
                result = get_powerlogs(file)
                self.assertTrue('sqlite_sequence' in result)


if __name__ == '__main__':
    unittest.main()
