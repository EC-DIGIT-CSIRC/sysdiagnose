from parsers.taskinfo import parse_path, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersTaskinfo(SysdiagnoseTestCase):

    def test_get_tasks(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            self.assertTrue(len(files) > 0)
            print(f'Parsing {files}')
            result = parse_path(log_root_path)
            self.assertGreater(len(result), 0)
            self.assertGreater(result['numb_tasks'], 0)
            self.assertGreater(len(result['tasks']), 0)
            numb_tasks = result['numb_tasks']
            len_tasks = len(result['tasks'])
            print(f"File says {numb_tasks} tasks - found {len_tasks} tasks, delta {numb_tasks - len_tasks}")
            # FIXME understand why numb_tasks is (almost) always 2 (once 3) less than len(tasks). Apple bug or mine? Or hidden processes?
            self.assertTrue((len_tasks > numb_tasks - 4))
            for task in result['tasks']:
                self.assertGreater(len(task['threads']), 0)


if __name__ == '__main__':
    unittest.main()
