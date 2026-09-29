import os
import tempfile
import unittest

from sysdiagnose.parsers.brctl import BrctlParser
from tests import SysdiagnoseTestCase


class TestParsersBrctl(SysdiagnoseTestCase):
    def test_parsebrctl(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                p = BrctlParser(self.sd.config, case=_case)

                if not p.is_compatible():
                    self.skipTest(f"Parser {p.module_name} not compatible with iOS {_case.get('ios_version')}")

                folders = p.get_log_files()
                if not folders:
                    self.fail(
                        f"No log files found for {case_id}: parser {p.module_name}, iOS {_case.get('ios_version')}"
                    )

                p.save_result(force=True)
                self.assertTrue(os.path.isfile(p.output_file))
                result = p.get_result()
                if result:
                    self.assertTrue("containers" in result)
                    self.assertTrue("boot_history" in result)
                    self.assertTrue("server_state" in result)
                    self.assertTrue("client_state" in result)
                    self.assertTrue("system" in result)
                    self.assertTrue("scheduler" in result)
                    self.assertTrue("applibrary" in result)
                    self.assertTrue("app_library_id" in result)
                    self.assertTrue("app_ids" in result)
                self.assert_result_summary_consistent(p, result)

    # real lines from brctl-container-list.txt of an iOS 16 sysdiagnose
    SAMPLE = (
        "listing 17 containers for account 89695A59-F596-4E3A-952F-034A30421C79:\n"
        "  id:com.apple.shoebox localizedName:'Wallet' "
        "documents:'/private/var/mobile/Library/Mobile Documents/com~apple~shoebox/Documents' "
        "[Private: inInitialState] clients: com.apple.passd, com.apple.PassbookUIService, com.apple.Passbook\n"
        "  id:com.apple.CloudDocs localizedName:'iCloud Drive' "
        "documents:'/private/var/mobile/Library/Mobile Documents/com~apple~CloudDocs' [Public:] clients: \n"
    )

    def test_parselistfile_keeps_values_containing_spaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "brctl-container-list.txt")
            with open(path, "w") as f:
                f.write(self.SAMPLE)
            containers = BrctlParser.parselistfile([path])["containers"]

        self.assertEqual(2, len(containers))

        shoebox, clouddocs = containers
        # a localizedName with a space must not be truncated at the space
        self.assertEqual("Wallet", shoebox["localizedName"])
        self.assertEqual("iCloud Drive", clouddocs["localizedName"])
        # the documents path must survive without the Mobile_Documents round-trip hack
        self.assertEqual(
            "/private/var/mobile/Library/Mobile Documents/com~apple~shoebox/Documents",
            shoebox["documents"],
        )
        # clients is a comma-separated list running to the end of the line, not just its first entry
        self.assertEqual(
            "com.apple.passd, com.apple.PassbookUIService, com.apple.Passbook",
            shoebox["clients"],
        )
        self.assertEqual("inInitialState", shoebox["Private"])
        self.assertEqual("", clouddocs["clients"])


if __name__ == "__main__":
    unittest.main()
