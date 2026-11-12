import json
import unittest

from sysdiagnose.utils import container_state as cs
from tests import synthetic_container_state as synth


def _parse(data, **kwargs):
    warnings = []
    rows = cs.parse_state_bytes(data, warn=warnings.append, **kwargs)
    return rows, warnings


def _app_data(rows):
    return [r for r in rows if r["record_type"] == "container" and r["container_class"] == "appData"]


class TestContainerStateCore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = synth.to_bytes(synth.build_state())
        cls.rows, cls.warnings = _parse(cls.raw, source_file="state.json")

    def test_counts_match_source(self):
        self.assertEqual(self.warnings, [])
        expected = {k: v for k, v in cs.expected_counts(json.loads(self.raw)).items() if v}
        self.assertEqual(cs.count_by_type(self.rows), expected)
        self.assertGreater(len(self.rows), 300)

    def test_every_record_type_present(self):
        present = set(cs.count_by_type(self.rows))
        self.assertEqual(present, set(cs.RECORD_TYPES) - {"unknown_section"})

    def test_stable_columns(self):
        for row in self.rows:
            self.assertEqual(tuple(row), cs.COLUMNS)

    def test_deterministic(self):
        again, _ = _parse(self.raw, source_file="state.json")
        self.assertEqual(json.dumps(self.rows, sort_keys=True), json.dumps(again, sort_keys=True))

    def test_container_state_and_time(self):
        containers = [r for r in self.rows if r["record_type"] == "container"]
        present = [r for r in containers if r["state"] == "present"]
        absent = [r for r in containers if r["state"] == "no_node"]
        self.assertTrue(present)
        self.assertTrue(absent)
        for row in present:
            self.assertTrue(row["timestamp_utc"].endswith("Z"))
            self.assertEqual(row["timestamp_utc"], row["birthtime"])
        for row in absent:
            self.assertEqual(row["timestamp_utc"], "")
            self.assertEqual(row["generation"], -1)

    def test_path_uses_path_identifier(self):
        row = _app_data(self.rows)[0]
        self.assertEqual(row["path"], f"/private/var/mobile/Containers/Data/Application/{row['path_identifier']}")
        self.assertNotEqual(row["uuid"], row["path_identifier"])

    def test_extension_parent_is_joined(self):
        plugin = [r for r in self.rows if r["record_type"] == "container" and r["container_class"] == "pluginData"]
        self.assertTrue(plugin)
        self.assertTrue(all(r["parent_identifier"] for r in plugin))

    def test_damaged_inputs_never_crash(self):
        for name, data in synth.edge_cases().items():
            with self.subTest(case=name):
                rows, _warnings = _parse(data)
                self.assertIsInstance(rows, list)

    def test_empty_and_truncated_warn_and_return_nothing(self):
        for name in ("empty_file", "truncated_json", "not_json", "root_is_list", "empty_object"):
            with self.subTest(case=name):
                rows, warnings = _parse(synth.edge_cases()[name])
                self.assertEqual(rows, [])
                self.assertTrue(warnings)

    def test_bad_timestamps_become_notes(self):
        rows, _ = _parse(synth.edge_cases()["bad_timestamps"])
        first = _app_data(rows)[:3]
        self.assertEqual(first[0]["timestamp_utc"], "")
        self.assertIn("birthtime: unparseable timestamp", first[0]["notes"])
        self.assertEqual(first[1]["timestamp_utc"], "")
        self.assertIn("out of range", first[1]["notes"])
        self.assertEqual(first[2]["timestamp_utc"], "2026-03-01T12:00:00.000Z")

    def test_timestamp_forms(self):
        self.assertEqual(cs.parse_timestamp("2026-03-01T14:00:00.000+02:00")[0], "2026-03-01T12:00:00.000Z")
        self.assertEqual(cs.parse_timestamp(1788000000)[0], "2026-08-29T10:40:00.000Z")
        self.assertEqual(cs.parse_timestamp(1788000000000)[0], "2026-08-29T10:40:00.000Z")
        self.assertEqual(cs.parse_timestamp(True)[0], "")
        self.assertEqual(cs.parse_timestamp(float("nan"))[0], "")
        self.assertEqual(cs.parse_timestamp(1e30)[0], "")
        self.assertEqual(cs.parse_timestamp("")[0], "")

    def test_huge_numbers_are_kept_as_text_or_dropped(self):
        rows, _ = _parse(synth.edge_cases()["huge_numbers"])
        container = next(r for r in rows if r["record_type"] == "container")
        self.assertEqual(container["generation"], str(10**30))
        self.assertIn("64-bit", container["notes"])
        client = next(r for r in rows if r["record_type"] == "client")
        self.assertEqual(client["generation"], "")

    def test_unknown_keys_are_kept_in_other(self):
        rows, warnings = _parse(synth.edge_cases()["unknown_keys"])
        self.assertTrue(warnings)
        container = next(r for r in rows if r["record_type"] == "container" and "futureField" in r["other"])
        self.assertIn("futureNodeField", container["other"])
        self.assertTrue(any(r["record_type"] == "unknown_section" for r in rows))
        codesign = next(r for r in rows if r["record_type"] == "codesign" and "futureFlag" in r["other"])
        self.assertTrue(codesign["identifier"])

    def test_flags_override_state(self):
        rows, _ = _parse(synth.edge_cases()["flags"])
        self.assertEqual([r["state"] for r in _app_data(rows)[:2]], ["corrupt", "ignored"])

    def test_missing_fields_are_noted(self):
        rows, _ = _parse(synth.edge_cases()["missing_fields"])
        notes = [r["notes"] for r in _app_data(rows)[:4]]
        self.assertIn("missing uuid", notes[0])
        self.assertIn("missing pathIdentifier", notes[1])
        self.assertIn("missing node", notes[2])
        self.assertIn("node missing", notes[3])


if __name__ == "__main__":
    unittest.main()
