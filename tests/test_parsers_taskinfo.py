import unittest

from parsers.taskinfo import get_tasks

class TestParsersTaskinfo(unittest.TestCase):

    log_path = "tests/testdata/iOS15/sysdiagnose_2023.05.24_13-29-15-0700_iPhone-OS_iPhone_19H349/taskinfo.txt"

    def test_get_tasks(self):
        result = get_tasks(self.log_path)
        self.assertGreater(len(result), 0)

        self.assertEqual(result['numb_tasks'], 244)
        self.assertGreater(len(result['tasks']), 0)


if __name__ == '__main__':
    unittest.main()
