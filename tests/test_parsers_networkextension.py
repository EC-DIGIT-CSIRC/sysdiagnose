from sysdiagnose.parsers.networkextension import NetworkExtensionParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersNetworkExtension(SysdiagnoseTestCase):

    def test_networkextension(self):
        for case_id, case in self.sd.cases().items():
            p = NetworkExtensionParser(self.sd.config, case_id=case_id)

            files = p.get_log_files()
            if not files:
                continue

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            self.assertTrue('Version' in result)


if __name__ == '__main__':
    unittest.main()
