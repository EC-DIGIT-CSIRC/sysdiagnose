from parsers.shutdownlogs import parse_shutdownlog, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersShutdownlogs(SysdiagnoseTestCase):

    def test_parse_shutdownlog(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            self.assertTrue(len(files) > 0)
            for file in files:
                print(f'Parsing {file}')
                result = parse_shutdownlog(file)
                self.assertGreater(len(result['data']), 0)
                for item in result['data']:
                    self.assertTrue('pid' in item)
                    self.assertTrue('path' in item)


if __name__ == '__main__':
    unittest.main()
