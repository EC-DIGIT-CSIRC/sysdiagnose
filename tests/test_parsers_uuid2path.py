from tests import SysdiagnoseTestCase
from parsers.uuid2path import parse_path, get_log_files
import unittest


class TestParsersUuid2path(SysdiagnoseTestCase):
    def test_uuid2path(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            if not files:  # not all sysdiagnose dumps have this log file
                continue

            print(f'Parsing {files}')
            result = parse_path(log_root_path)
            self.assertGreater(len(result), 0)


if __name__ == '__main__':
    unittest.main()
