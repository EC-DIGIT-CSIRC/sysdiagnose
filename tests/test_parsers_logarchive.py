from parsers.logarchive import get_log_files, parse_path, parse_path_to_folder
from tests import SysdiagnoseTestCase
import os
import platform
import tempfile
import unittest


class TestParsersLogarchive(SysdiagnoseTestCase):

    def test_get_logs_outputdir(self):
        for log_root_path in self.log_root_paths:
            folders = get_log_files(log_root_path)
            for folder in folders:
                with tempfile.TemporaryDirectory() as tmp_outpath:
                    print(f'Parsing {folder} to {tmp_outpath}')
                    result = parse_path_to_folder(folder, output=tmp_outpath)
                    # check if folder is not empty
                    self.assertNotEqual(os.listdir(os.path.join(tmp_outpath, "logarchive")), [])
                    # result should contain at least one entry (linux = stdout, mac = mention it's saved to a file)
                    self.assertTrue(result)

                    if (platform.system() == "Darwin"):
                        self.assertTrue(os.path.isfile(os.path.join(tmp_outpath, "logarchive", "logarchive.json")))
                    else:
                        self.assertTrue(os.path.isfile(os.path.join(tmp_outpath, "logarchive", "liveData.json")))

    def test_get_logs_result(self):
        for log_root_path in self.log_root_paths:
            folders = get_log_files(log_root_path)
            for folder in folders:
                print(f'Parsing {folder}')
                result = parse_path(folder)
                # FIXME check result on a mac
                self.assertGreater(len(result), 0)


if __name__ == '__main__':
    unittest.main()
