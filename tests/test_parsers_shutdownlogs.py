from parsers.shutdownlogs import parse_path, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersShutdownlogs(SysdiagnoseTestCase):

    def test_parse_shutdownlog(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            self.assertTrue(len(files) > 0)
            print(f'Parsing {files}')
            result = parse_path(log_root_path)
            self.assertGreater(len(result), 0)
            for shutdown in result.values():
                for process in shutdown:
                    self.assertTrue('pid' in process)
                    self.assertTrue('path' in process)


if __name__ == '__main__':
    unittest.main()
