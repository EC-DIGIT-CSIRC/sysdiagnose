from tests import SysdiagnoseTestCase
from parsers.uuid2path import parse_path, get_log_files
import unittest


class TestParsersUuid2path(SysdiagnoseTestCase):
    def test_get_tasks(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            if files:  # not all sysdiagnose dumps have this log file
                for file in files:
                    print(f'Parsing {file}')
                    result = parse_path(file)
                    self.assertGreater(len(result), 0)


if __name__ == '__main__':
    unittest.main()
