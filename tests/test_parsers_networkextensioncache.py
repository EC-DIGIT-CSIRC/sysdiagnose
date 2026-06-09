import os
import unittest

from sysdiagnose.parsers.networkextensioncache import NetworkExtensionCacheParser
from tests import SysdiagnoseTestCase


class TestParsersNetworkExtensionCache(SysdiagnoseTestCase):
    def test_networkextensioncache(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                p = NetworkExtensionCacheParser(self.sd.config, case_id=case_id)
                files = p.get_log_files()
                if not files:
                    self.fail(
                        f"No log files found for {case_id}: parser {p.module_name}, iOS {_case.get('ios_version')}"
                    )
                    self.skipTest(f"No log files found for {case_id}")

                p.save_result(force=True)
                self.assertTrue(os.path.isfile(p.output_file))

                # TODO find a way to validate the result and check if the parser works.
                # we may need to check if the original file is greater than X, and then require that the result contains some keys
                result = p.get_result()
                self.assert_result_summary_consistent(p, result)


if __name__ == "__main__":
    unittest.main()
