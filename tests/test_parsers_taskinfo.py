from parsers.taskinfo import TaskinfoParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersTaskinfo(SysdiagnoseTestCase):

    def test_get_tasks(self):
        for case_id, case in self.sd.cases().items():
            p = TaskinfoParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            self.assertGreater(len(result), 0)
            # self.assertGreater(result['numb_tasks'], 0)
            # self.assertGreater(len(result['tasks']), 0)
            # numb_tasks = result['numb_tasks']
            # len_tasks = len(result['tasks'])
            # print(f"File says {numb_tasks} tasks - found {len_tasks} tasks, delta {numb_tasks - len_tasks}")
            # # a delta is not abnormal, as numb_tasks seems to be taking the count from "ps".
            # # "ps" always has at least two processes running (ps and psauxwww)
            # # Execution of taskinfo happens at another moment, so other processes may have started/stopped
            # self.assertAlmostEqual(len_tasks, numb_tasks, delta=4)
            # for task in result['tasks']:
            #     self.assertGreater(len(task['threads']), 0)


if __name__ == '__main__':
    unittest.main()
