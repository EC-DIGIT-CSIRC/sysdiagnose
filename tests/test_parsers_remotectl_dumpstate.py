from parsers.remotectl_dumpstate import parse_path, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersRemotectlDumpstate(SysdiagnoseTestCase):

    def test_get_remotectldumpstate(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            print(f'Parsing {files}')
            parse_path(log_root_path)
            # just test for no exceptions


if __name__ == '__main__':
    unittest.main()
