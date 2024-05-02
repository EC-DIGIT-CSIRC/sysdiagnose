from parsers.brctl import parsebrctl, get_log_files
from tests import SysdiagnoseTestCase
import unittest


class TestParsersBrctl(SysdiagnoseTestCase):

    def test_parsebrctl(self):
        for log_root_path in self.log_root_paths:
            if 'iOS15' in log_root_path:  # FIXME - this is a hack to skip iOS15 logs, do it cleanly
                print(f"Skipping iOS15 logs: {log_root_path}")
                continue

            folders = get_log_files(log_root_path)
            for folder in folders:
                print(f'Parsing {folder}')
                result = parsebrctl(folder)
                self.assertTrue('containers' in result)
                self.assertTrue('boot_history' in result)
                self.assertTrue('server_state' in result)
                self.assertTrue('client_state' in result)
                self.assertTrue('system' in result)
                self.assertTrue('applibrary' in result)
                self.assertTrue('app_library_id' in result)
                self.assertTrue('app_ids' in result)


if __name__ == '__main__':
    unittest.main()
