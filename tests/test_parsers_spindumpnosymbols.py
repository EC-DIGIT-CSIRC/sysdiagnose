from parsers.spindumpnosymbols import parsespindumpNS, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersSpindumpnosymbols(SysdiagnoseTestCase):

    def test_parsespindumpNS(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            self.assertTrue(len(files) > 0)
            for file in files:
                print(f'Parsing {file}')
                result = parsespindumpNS(file)
                self.assertGreater(len(result), 0)
                self.assertTrue('OS Version' in result)
                self.assertGreater(len(result['processes']), 0)


if __name__ == '__main__':
    unittest.main()
