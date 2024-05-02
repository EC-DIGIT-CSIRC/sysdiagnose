from parsers.taskinfo import get_tasks, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersTaskinfo(SysdiagnoseTestCase):

    def test_get_tasks(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            self.assertTrue(len(files) > 0)
            for file in files:
                print(f'Parsing {file}')
                result = get_tasks(file)
                self.assertGreater(len(result), 0)
                self.assertGreater(result['numb_tasks'], 0)
                self.assertGreater(len(result['tasks']), 0)


if __name__ == '__main__':
    unittest.main()
