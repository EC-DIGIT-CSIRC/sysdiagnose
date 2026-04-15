from sysdiagnose.analysers.plist_rules import PlistRulesAnalyser
from tests import SysdiagnoseTestCase
import unittest
from unittest.mock import patch
import os


class TestAnalysersPlistRules(SysdiagnoseTestCase):

    def setUp(self):
        super().setUp()
        self.yara_rules_folder = os.path.join(self.tmp_folder, 'yara_plist_rules')
        os.makedirs(self.yara_rules_folder, exist_ok=True)

        # Rule that matches on a string commonly found in parsed plist JSON
        rule_content = """
rule match_plist_product_name {
    meta:
        description = "Matches on ProductName key typically found in SystemVersion plist"
        author = "test"
    strings:
        $a = "ProductName"
    condition:
        $a
}
"""
        rule_file_path = os.path.join(self.yara_rules_folder, 'test_plist_rule.yar')
        with open(rule_file_path, 'w') as rule_file:
            rule_file.write(rule_content)

    def test_analyse_plist_rules(self):
        with patch.dict(os.environ, {'SYSDIAGNOSE_PLIST_RULES_PATH': self.yara_rules_folder}):
            for case_id, case in self.sd.cases().items():
                print(f"Running PlistRules for {case_id}")
                a = PlistRulesAnalyser(self.sd.config, case_id=case_id)
                a.save_result(force=True)
                self.assertTrue(os.path.isfile(a.output_file))

                result = a.get_result()
                self.assertIsInstance(result, list)
                # We expect at least one match on the ProductName string
                self.assertGreater(len(result), 0)
                for item in result:
                    self.assert_has_required_fields_jsonl(item)
                    # Verify structured plist data is included
                    self.assertIn('plist_data', item['data'])
                    self.assertIn('yara_rule', item['data'])
                    self.assertIn('plist_file', item['data'])

    def test_analyse_plist_rules_no_rules_folder(self):
        with patch.dict(os.environ, {'SYSDIAGNOSE_PLIST_RULES_PATH': '/nonexistent/path'}):
            for case_id, case in self.sd.cases().items():
                a = PlistRulesAnalyser(self.sd.config, case_id=case_id)
                with self.assertRaises(FileNotFoundError):
                    a.get_result(force=True)
                break  # only need to test once


if __name__ == '__main__':
    unittest.main()
