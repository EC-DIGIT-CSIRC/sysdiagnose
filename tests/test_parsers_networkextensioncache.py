from sysdiagnose.parsers.networkextensioncache import NetworkExtensionCacheParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersNetworkExtensionCache(SysdiagnoseTestCase):

    def test_networkextensioncache(self):
        for case_id, case in self.sd.cases().items():
            p = NetworkExtensionCacheParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            if not files:
                continue

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            # TODO find a way to validate the result and check if the parser works.
            # we may need to check if the original file is greater than X, and then require that the result contains some keys


if __name__ == '__main__':
    unittest.main()
