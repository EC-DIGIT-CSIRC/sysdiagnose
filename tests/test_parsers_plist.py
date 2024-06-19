from parsers.plists import parse_path, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersPlist(SysdiagnoseTestCase):

    def test_get_plists(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            self.assertGreater(len(files), 0)
            print(f'Parsing {files}')
            result = parse_path(log_root_path)
            self.assertGreater(len(result), 0)
            print(result.keys())
            self.assertIn('hidutil.plist', result.keys())
            # nothing specific to assert here as there's not always a result
            # just catching exceptions


if __name__ == '__main__':
    unittest.main()
