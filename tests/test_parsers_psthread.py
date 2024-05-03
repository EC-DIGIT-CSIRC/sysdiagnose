from parsers.psthread import parse_ps_thread, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersPsthread(SysdiagnoseTestCase):

    def test_parse_psthread(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            self.assertTrue(len(files) > 0)
            for file in files:
                print(f'Parsing {file}')
                result = parse_ps_thread(file)
                if result:  # not all logs contain data
                    for item in result:
                        self.assertTrue('COMMAND' in item)
                        self.assertTrue('PID' in item)
                        self.assertTrue('USER' in item)


if __name__ == '__main__':
    unittest.main()
