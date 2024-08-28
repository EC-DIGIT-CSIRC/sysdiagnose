from parsers.networkextension import NetworkExtensionParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersNetworkExtension(SysdiagnoseTestCase):

    def test_networkextension(self):
        for case_id, case in self.sd.cases().items():
            p = NetworkExtensionParser(self.sd.config, case_id=case_id)

            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            # TODO below needs to be changed if https://github.com/ydkhatri/nska_deserialize/pull/3 is merged
            # self.assertTrue('Version' in result)
            seen = False
            for entry in result:
                if 'Version' in entry:
                    seen = True
                    break
            self.assertTrue(seen)


if __name__ == '__main__':
    unittest.main()
