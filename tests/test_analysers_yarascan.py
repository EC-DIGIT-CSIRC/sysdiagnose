from sysdiagnose.analysers.yarascan import YaraAnalyser
from tests import SysdiagnoseTestCase
import unittest
from unittest.mock import patch
import os


class TestAnalysersYarascan(SysdiagnoseTestCase):

    def setUp(self):
        super().setUp()
        self.yara_rules_folder = os.path.join(self.tmp_folder, 'yararules')
        os.makedirs(self.yara_rules_folder, exist_ok=True)
        # Create a dummy YARA rule file for testing
        rule_content = """
rule match_for_sure_on_serial_number {
    strings:
        $a = "F4GT2K24HG7K"
    condition:
        $a
}
"""
        rule_file_path = os.path.join(self.yara_rules_folder, 'test_rule.yar')
        with open(rule_file_path, 'w') as rule_file:
            rule_file.write(rule_content)

    def test_analyse_yarascan(self):
        with patch.dict(os.environ, {'SYSDIAGNOSE_YARA_RULES_PATH': self.yara_rules_folder}):
            for case_id, case in self.sd.cases().items():
                print(f"Running Yarascan for {case_id}")
                # run the analyser
                a = YaraAnalyser(self.sd.config, case_id=case_id)
                a.save_result(force=True)
                self.assertTrue(os.path.isfile(a.output_file))

                result = a.get_result()
                for item in result:
                    self.assert_has_required_fields_jsonl(item)


if __name__ == '__main__':
    unittest.main()
