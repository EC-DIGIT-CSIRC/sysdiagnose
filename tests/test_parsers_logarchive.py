import os
import platform
import tempfile
import unittest

from parsers.logarchive import get_logs

class TestParsersLogarchive(unittest.TestCase):

    log_path = "tests/testdata/sysdiagnose_2023.05.24_13-29-15-0700_iPhone-OS_iPhone_19H349/system_logs.logarchive"

    def test_get_logs_outputdir(self):
        with tempfile.TemporaryDirectory() as tmp_outpath:
            result = get_logs(self.log_path, output=tmp_outpath)
            # check if folder is not empty
            self.assertNotEqual(os.listdir(tmp_outpath), [])

            if (platform.system() == "Darwin"):
                self.assertTrue(os.path.isfile(os.path.join(tmp_outpath, "logarchive.json")))
            else:
                self.assertTrue(os.path.isfile(os.path.join(tmp_outpath, "liveData.json")))

    def test_get_logs_result(self):
        result = get_logs(self.log_path)
        # FIXME check result on a mac
        self.assertGreater(len(result), 0)

if __name__ == '__main__':
    unittest.main()