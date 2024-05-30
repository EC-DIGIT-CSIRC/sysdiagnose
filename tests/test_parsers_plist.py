from parsers.plists import parse_path, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersPlist(SysdiagnoseTestCase):

    def test_get_plists(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            for file in files:
                print(f'Parsing {file}')
                parse_path(file)
                # nothing specific to assert here as there's not always a result
                # just catching exceptions


if __name__ == '__main__':
    unittest.main()
