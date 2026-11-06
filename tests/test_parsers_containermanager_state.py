import os
import tempfile
import unittest

from sysdiagnose.parsers.containermanager_state import STATE_FILE, ContainerManagerStateParser
from sysdiagnose.utils.base import SysdiagnoseConfig
from tests import SysdiagnoseTestCase
from tests import synthetic_container_state as synth

SYSDIAGNOSE_LOG = "spindump_sysdiagnose_2026.09.29_19-00-00-0400_iPhone-OS_iPhone_00A000.txt\n"


def _make_case(root: str, content: bytes | None, case_id: str = "synthetic", ios_version: str = "27.0"):
    """Build a minimal SAF case on disk around a synthetic (fabricated) state.json."""
    config = SysdiagnoseConfig(cases_path=root)
    data = config.get_case_data_folder(case_id)
    folder = os.path.join(data, "sysdiagnose_synthetic")
    os.makedirs(os.path.join(folder, "logs", "ContainerManager"), exist_ok=True)
    with open(os.path.join(folder, "sysdiagnose.log"), "w") as handle:
        handle.write(SYSDIAGNOSE_LOG)
    if content is not None:
        with open(os.path.join(folder, STATE_FILE), "wb") as handle:
            handle.write(content)
    return config, {"case_id": case_id, "ios_version": ios_version}


class TestParsersContainermanagerStateSynthetic(unittest.TestCase):
    """Runs against a fabricated file; needs no sysdiagnose test archive."""

    def test_synthetic_file(self):
        with tempfile.TemporaryDirectory() as root:
            config, case = _make_case(root, synth.to_bytes(synth.build_state()))
            parser = ContainerManagerStateParser(config, case)
            self.assertTrue(parser.is_compatible())
            self.assertEqual(len(parser.get_log_files()), 1)
            parser.save_result(force=True)
            self.assertTrue(os.path.isfile(parser.output_file))
            result = parser.get_result()
            self.assertGreater(len(result), 300)
            kinds = {item["data"]["record_type"] for item in result}
            self.assertTrue({"container", "codesign", "child_parent", "client", "class_path", "persona"} <= kinds)
            for item in result:
                for field in ("datetime", "message", "timestamp_desc", "module"):
                    self.assertIn(field, item)
                self.assertEqual(item["module"], "containermanager_state")
            untimed = [i for i in result if i["data"]["record_type"] == "child_parent"]
            self.assertTrue(untimed)
            self.assertTrue(all(i["datetime"].startswith("2026-09-29T") for i in untimed))
            self.assertEqual(parser.get_result_summary().num_events, len(result))

    def test_missing_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as root:
            config, case = _make_case(root, None)
            parser = ContainerManagerStateParser(config, case)
            self.assertEqual(parser.get_log_files(), [])
            self.assertEqual(parser.execute(), [])

    def test_damaged_files_return_empty_without_raising(self):
        for name in ("empty_file", "truncated_json", "root_is_list", "not_json"):
            with self.subTest(case=name), tempfile.TemporaryDirectory() as root:
                config, case = _make_case(root, synth.edge_cases()[name])
                self.assertEqual(ContainerManagerStateParser(config, case).execute(), [])

    def test_old_ios_is_skipped(self):
        with tempfile.TemporaryDirectory() as root:
            config, case = _make_case(root, None, ios_version="26.6")
            self.assertFalse(ContainerManagerStateParser(config, case).is_compatible())


class TestParsersContainermanagerState(SysdiagnoseTestCase):
    def test_parse_state(self):
        compatible = []
        for case_id, _case in self.sd.cases().items():
            p = ContainerManagerStateParser(self.sd.config, case=_case)
            if p.is_compatible():
                compatible.append((case_id, _case, p))
        if not compatible:
            self.skipTest("No iOS 27 case in the test data (the file only exists from iOS 27)")

        for case_id, _case, p in compatible:
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                files = p.get_log_files()
                if not files:
                    self.fail(
                        f"No log files found for {case_id}: parser {p.module_name}, iOS {_case.get('ios_version')}"
                    )

                p.save_result(force=True)
                self.assertTrue(os.path.isfile(p.output_file))

                result = p.get_result()
                self.assertGreater(len(result), 0)
                for item in result:
                    self.assertIn("record_type", item["data"])
                    self.assert_has_required_fields_jsonl(item)
                self.assert_result_summary_consistent(p, result)


if __name__ == "__main__":
    unittest.main()
