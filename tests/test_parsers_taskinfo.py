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
            # a delta is not abnormal, as numb_tasks seems to be taking the count from "ps".
            # "ps" always has at least two processes running (ps and psauxwww)
            # Execution of taskinfo happens at another moment, so other processes may have started/stopped
            self.assertAlmostEqual(len_tasks, numb_tasks, delta=4)
            for task in result['tasks']:
                self.assertGreater(len(task['threads']), 0)


if __name__ == '__main__':
    unittest.main()
