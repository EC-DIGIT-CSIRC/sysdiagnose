import os
import unittest

from sysdiagnose.parsers.lsaw_csstoredump import LsawCsstoredumpParser
from tests import SysdiagnoseTestCase


class TestParsersLsawCsstoredump(SysdiagnoseTestCase):
    def test_parse_lsaw_csstoredump(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                p = LsawCsstoredumpParser(self.sd.config, case=_case)

                if not p.is_compatible():
                    self.skipTest(f"Parser {p.module_name} not compatible with iOS {_case.get('ios_version')}")

                files = p.get_log_files()
                if not files:
                    self.fail(
                        f"No log files found for {case_id}: parser {p.module_name}, iOS {_case.get('ios_version')}"
                    )

                p.save_result(force=True)
                result = p.get_result()
                self.assert_result_summary_consistent(p, result)

                self.assertTrue(os.path.isfile(p.output_file))

                for item in result:
                    self.assert_has_required_fields_jsonl(item)

    def test_parse_nsstring(self):
        lines = [
            "bundle id:                  foo (0x358)",
            "class:                      kLSBundleClassApplication (0x2)",
            "container:                  /cores/binpack/Applications/ (0x10)",
            "displayVersion:             1.0",
            "mod date:                   2023-03-20 22:40 (POSIX 1679377209, 𝛥 2mths 5days 14hr 49min 18sec)",
            "reg date:                   2023-05-24 13:25 (POSIX 1684959955, 𝛥 3min 32sec)",
            "rec mod date:               2023-05-24 13:25 (POSIX 1684959955, 𝛥 3min 32sec)",
            "** foo bar hello world this is sometimes happening **",
            "bundle flags:               has-display-name  requires-iphone-os  shows-sec-prompts (0000000000001002)",
            "platform:                   native",
            "iconName:                   AppIcon",
            "iconDict:                   1 values (11728 (0x2dd0))",
            "                            {",
            "                                CFBundlePrimaryIcon =     {",
            "                                    CFBundleIconFiles =         (",
            "                                        AppIcon60x60",
            "                                    );",
            "                                    CFBundleIconName = AppIcon;",
            "                                };",
            "                            }",
            "executable:                 foo",
            "--------------------------------------------------------------------------------",
            "foo_1:                        hello",
            "foo_2:                        world",
            "--------------------------------------------------------------------------------",
            "foo_1:                        hello2",
            "foo_2:                        world2",
        ]
        expected_result = {
            "bundle id": "foo (0x358)",
            "class": "kLSBundleClassApplication (0x2)",
            "container": "/cores/binpack/Applications/ (0x10)",
            "displayVersion": "1.0",
            "mod date": "2023-03-20 22:40 (POSIX 1679377209, 𝛥 2mths 5days 14hr 49min 18sec)",
            "reg date": "2023-05-24 13:25 (POSIX 1684959955, 𝛥 3min 32sec)",
            "rec mod date": "2023-05-24 13:25 (POSIX 1684959955, 𝛥 3min 32sec)",
            "bundle flags": "has-display-name  requires-iphone-os  shows-sec-prompts (0000000000001002)",
            "platform": "native",
            "iconName": "AppIcon",
            "iconDict": "1 values (11728 (0x2dd0)) { CFBundlePrimaryIcon =     { CFBundleIconFiles =         ( AppIcon60x60 ); CFBundleIconName = AppIcon; }; }",
            "executable": "foo",
            "record_data": [
                "** foo bar hello world this is sometimes happening **",
                {"foo_1": "hello", "foo_2": "world"},
                {"foo_1": "hello2", "foo_2": "world2"},
            ],
        }
        result = LsawCsstoredumpParser.parse_plist_NSString(lines)
        self.maxDiff = None
        self.assertEqual(expected_result, result)

    def test_parse_nsstring_2(self):
        lines = [
            "table ID:                   24",
            "name:                       Container",
            "bytes:                      0xccb24",
            "length:                     72",
            "unit count:                 3",
            "IdentifierCache:            CSStore2::HashMap<unsigned int, unsigned int, CSStore2::_IdentifierFunctions, 1> @ 0xccb88 { buckets = 16, count = 25 }",
            "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++",
            "0x00000000 000ccb1c:	06000040 48000000 436f6e74 61696e65    ···@H···Containe",
            "0x00000000 000ccb2c:	72000000 00000000 00000000 00000000    r···············",
            "0x00000000 000ccb3c:	00000000 00000000 00000000 00000000    ················",
            "0x00000000 000ccb4c:	00000000 00000000 00000000 00000000    ················",
            "0x00000000 000ccb5c:	00000000 00000000 04000000 88cb0c00    ················",
        ]
        expected_result = {
            "table ID": "24",
            "name": "Container",
            "bytes": "0xccb24",
            "length": "72",
            "unit count": "3",
            "IdentifierCache": "CSStore2::HashMap<unsigned int, unsigned int, CSStore2::_IdentifierFunctions, 1> @ 0xccb88 { buckets = 16, count = 25 }",
            "record_data": [
                "0x00000000 000ccb1c:\t06000040 48000000 436f6e74 61696e65    ···@H···Containe",
                "0x00000000 000ccb2c:\t72000000 00000000 00000000 00000000    r···············",
                "0x00000000 000ccb3c:\t00000000 00000000 00000000 00000000    ················",
                "0x00000000 000ccb4c:\t00000000 00000000 00000000 00000000    ················",
                "0x00000000 000ccb5c:\t00000000 00000000 04000000 88cb0c00    ················",
            ],
        }

        result = LsawCsstoredumpParser.parse_plist_NSString(lines)
        self.maxDiff = None
        self.assertEqual(expected_result, result)


if __name__ == "__main__":
    unittest.main()
