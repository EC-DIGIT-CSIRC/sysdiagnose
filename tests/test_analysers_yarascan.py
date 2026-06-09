import os
import unittest
from unittest.mock import patch

from sysdiagnose.analysers.yarascan import YaraAnalyser
from tests import SysdiagnoseTestCase


class TestAnalysersYarascan(SysdiagnoseTestCase):
    def setUp(self):
        super().setUp()
        self.yara_rules_folder = os.path.join(self.tmp_folder, "yararules")
        os.makedirs(self.yara_rules_folder, exist_ok=True)
        # Create a dummy YARA rule file for testing, one that should match at least (only?) on sysdiagnose.log file.
        # Avoids relying on any specific content and potential too many matches.
        # Failure of this rule will help us to detect a change in the binary too :)
        rule_content = """
rule match_for_sure_on_sysdiagnose_version {
    strings:
        $a = "sysdiagnose version 3.0"
    condition:
        $a
}
"""
        rule_file_path = os.path.join(self.yara_rules_folder, "test_rule.yar")
        with open(rule_file_path, "w") as rule_file:
            rule_file.write(rule_content)

    def test_analyse_yarascan(self):
        with patch.dict(os.environ, {"SYSDIAGNOSE_YARA_RULES_PATH": self.yara_rules_folder}):
            for case_id, _case in self.sd.cases().items():
                with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                    print(f"Running Yarascan for {case_id}")
                    # run the analyser
                    a = YaraAnalyser(self.sd.config, case_id=case_id)
                    a.save_result(force=True)
                    self.assertTrue(os.path.isfile(a.output_file))

                    result = a.get_result()
                    for item in result:
                        self.assert_has_required_fields_jsonl(item)
                    self.assert_result_summary_consistent(a, result)


if __name__ == "__main__":
    unittest.main()
