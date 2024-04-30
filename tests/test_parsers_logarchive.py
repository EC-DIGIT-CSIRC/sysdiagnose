from parsers.logarchive import get_logs
from tests import SysdiagnoseTestCase
import os
import platform
import tempfile
import unittest


class TestParsersLogarchive(SysdiagnoseTestCase):

    log_path = "tests/testdata/iOS15/sysdiagnose_2023.05.24_13-29-15-0700_iPhone-OS_iPhone_19H349/system_logs.logarchive"

    def test_get_logs_outputdir(self):
        with tempfile.TemporaryDirectory() as tmp_outpath:
            result = get_logs(self.log_path, output=tmp_outpath)
            # check if folder is not empty
            self.assertNotEqual(os.listdir(tmp_outpath), [])
            # result should contain at least one entry (linux = stdout, mac = mention it's saved to a file)
            self.assertTrue(len(result['data']) > 0)

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
