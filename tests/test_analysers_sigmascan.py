import os
import tempfile
import unittest
from unittest.mock import patch

from sysdiagnose.analysers.sigmascan import SigmascanAnalyser, build_summary
from sysdiagnose.sigmascan.emit import build_alert
from sysdiagnose.sigmascan.loader import load_rule_from_yaml
from tests import SysdiagnoseTestCase

# NOTE: generic placeholder detection content; public SAF module names are fine.


def _write_rule(dir_path: str, name: str, text: str) -> None:
    with open(os.path.join(dir_path, name), "w") as f:
        f.write(text)


# A rule that matches essentially any event (keyword over a very common letter) — used to
# guarantee hits on a real case without depending on specific content.
MATCH_ANYTHING = """
title: Match anything (test)
id: 11111111-1111-4111-8111-111111111111
status: experimental
level: low
logsource:
  product: ios
detection:
  keywords:
    - e
  condition: keywords
"""

# A rule that matches nothing (a token that will not appear in any event).
MATCH_NOTHING = """
title: Match nothing (test)
id: 22222222-2222-4222-8222-222222222222
status: stable
level: high
logsource:
  product: ios
detection:
  keywords:
    - ZZZZ_NO_SUCH_TOKEN_QX9
  condition: keywords
"""


class TestSigmascanAnalyserEndToEnd(SysdiagnoseTestCase):
    def test_runs_and_emits_valid_alerts(self):
        with tempfile.TemporaryDirectory() as rules_dir:
            _write_rule(rules_dir, "match.yml", MATCH_ANYTHING)
            with patch.dict(os.environ, {"SYSDIAGNOSE_SIGMA_RULES_PATH": rules_dir}):
                for case_id, _case in self.sd.cases().items():
                    with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                        a = SigmascanAnalyser(self.sd.config, case=_case)
                        if not a.is_compatible():
                            self.skipTest(f"not compatible with iOS {_case.get('ios_version')}")

                        a.save_result(force=True)
                        self.assertTrue(os.path.isfile(a.output_file))
                        result = a.get_result()

                        # Expect at least one alert (the match-anything rule).
                        self.assertGreater(len(result), 0, "expected at least one alert")
                        for item in result:
                            self.assert_has_required_fields_jsonl(item)
                            self.assertEqual(item["module"], "sigmascan")
                            data = item["data"]
                            self.assertEqual(data["rule_id"], "11111111-1111-4111-8111-111111111111")
                            self.assertEqual(data["level"], "low")
                            self.assertIn("event", data)  # full event embedded
                            self.assertIn("matched_module", data)
                        self.assert_result_summary_consistent(a, result)

    def test_zero_matches_yields_empty_output(self):
        with tempfile.TemporaryDirectory() as rules_dir:
            _write_rule(rules_dir, "nomatch.yml", MATCH_NOTHING)
            with patch.dict(os.environ, {"SYSDIAGNOSE_SIGMA_RULES_PATH": rules_dir}):
                for case_id, _case in self.sd.cases().items():
                    with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                        a = SigmascanAnalyser(self.sd.config, case=_case)
                        if not a.is_compatible():
                            self.skipTest(f"not compatible with iOS {_case.get('ios_version')}")

                        a.save_result(force=True)
                        result = a.get_result()
                        # Zero matches = empty output (not an error, no placeholder record).
                        self.assertEqual(result, [])
                        self.assert_result_summary_consistent(a, result)

    def test_no_rules_dir_yields_empty_output(self):
        with patch.dict(os.environ, {"SYSDIAGNOSE_SIGMA_RULES_PATH": "/nonexistent/sigma/rules"}):
            for case_id, _case in self.sd.cases().items():
                with self.subTest(case_id=case_id):
                    a = SigmascanAnalyser(self.sd.config, case=_case)
                    if not a.is_compatible():
                        self.skipTest("incompatible")
                    a.save_result(force=True)
                    self.assertEqual(a.get_result(), [])

    def test_empty_rules_dir_does_not_mark_run_as_error(self):
        # No rules is an operator-config state, not an execution failure: the analyser run
        # must NOT be ERROR (it would be if "no rules" were logged at error level, since SAF
        # folds logger.error into the summary status).
        from sysdiagnose.utils.summary import ExecutionStatus

        with (
            tempfile.TemporaryDirectory() as empty_dir,
            patch.dict(os.environ, {"SYSDIAGNOSE_SIGMA_RULES_PATH": empty_dir}),
        ):
            for case_id, _case in self.sd.cases().items():
                with self.subTest(case_id=case_id):
                    a = SigmascanAnalyser(self.sd.config, case=_case)
                    if not a.is_compatible():
                        self.skipTest("incompatible")
                    a.save_result(force=True)
                    self.assertEqual(a.get_result(), [])
                    self.assertNotEqual(a.get_result_summary().status, ExecutionStatus.ERROR)


class TestBuildSummary(unittest.TestCase):
    """Pure tests over build_summary."""

    def _alert(self, rule_id: str, title: str, level: str) -> dict:
        return {"module": "sigmascan", "data": {"rule_id": rule_id, "rule_title": title, "level": level}}

    def test_all_five_levels_always_present(self):
        summary = build_summary([])
        self.assertEqual(set(summary), {"critical", "high", "medium", "low", "informational"})
        for level in summary.values():
            self.assertEqual(level["count"], 0)
            self.assertEqual(level["rules"], [])

    def test_counts_and_per_rule_breakdown(self):
        alerts = (
            [self._alert("id-a", "Rule A", "critical")] * 50
            + [self._alert("id-b", "Rule B", "critical")] * 1
            + [self._alert("id-c", "Rule C", "high")] * 1
        )
        summary = build_summary(alerts)
        self.assertEqual(summary["critical"]["count"], 51)
        self.assertEqual(summary["high"]["count"], 1)
        self.assertEqual(summary["medium"]["count"], 0)
        # sorted by count desc -> Rule A first
        crit_rules = summary["critical"]["rules"]
        self.assertEqual(crit_rules[0]["id"], "id-a")
        self.assertEqual(crit_rules[0]["count"], 50)
        self.assertEqual(crit_rules[1]["id"], "id-b")

    def test_invariant_count_equals_sum_of_rules(self):
        alerts = [self._alert("id-a", "A", "medium")] * 3 + [self._alert("id-b", "B", "medium")] * 7
        summary = build_summary(alerts)
        for level in summary.values():
            self.assertEqual(level["count"], sum(r["count"] for r in level["rules"]))

    def test_unknown_level_bucketed_informational(self):
        alerts = [self._alert("id-x", "X", "bogus-level")]
        summary = build_summary(alerts)
        self.assertEqual(summary["informational"]["count"], 1)

    def test_missing_level_bucketed_informational(self):
        alerts = [{"module": "sigmascan", "data": {"rule_id": "id-y", "rule_title": "Y"}}]
        summary = build_summary(alerts)
        self.assertEqual(summary["informational"]["count"], 1)


class TestLoadModuleEvents(SysdiagnoseTestCase):
    """_load_module_events must accept every shape get_result() can return — crucially a
    GENERATOR (logarchive streams its events via a generator, not a list). A regression
    guard: a generator source must be scanned, not skipped as 'not a dict/list'."""

    def _analyser(self):
        case = next(iter(self.sd.cases().values()))
        return SigmascanAnalyser(self.sd.config, case=case)

    def _patch_module(self, result):
        """Patch get_module_class to return a fake class whose get_result() yields `result`
        and whose output_exists() is True."""

        class _Fake:
            format = "jsonl"

            def __init__(self, config, case):
                pass

            def output_exists(self):
                return True

            def get_result(self):
                return result

        return patch.object(self.sd.config, "get_module_class", return_value=_Fake)

    def test_generator_result_is_iterated_not_skipped(self):
        a = self._analyser()

        def gen():
            yield {"message": "a", "data": {}}
            yield {"message": "b", "data": {}}

        with self._patch_module(gen()):
            events = a._load_module_events("anymod")
            self.assertIsNotNone(events, "a generator source must NOT be skipped")
            materialised = list(events)
            self.assertEqual(len(materialised), 2)

    def test_list_result(self):
        a = self._analyser()
        with self._patch_module([{"message": "a", "data": {}}]):
            self.assertEqual(len(list(a._load_module_events("m"))), 1)

    def test_dict_result_wrapped_as_single_event(self):
        a = self._analyser()
        with self._patch_module({"some": "object"}):
            events = list(a._load_module_events("m"))
            self.assertEqual(events, [{"some": "object"}])

    def test_str_result_skipped(self):
        a = self._analyser()
        with self._patch_module("custom text output"):
            self.assertIsNone(a._load_module_events("m"))


class TestCompileOnce(SysdiagnoseTestCase):
    """Each rule must be compiled exactly once per run, even an all-modules rule that is
    scanned against many modules (otherwise it would be recompiled once per module)."""

    def test_all_modules_rule_compiled_once(self):
        import sysdiagnose.analysers.sigmascan as mod

        with tempfile.TemporaryDirectory() as rules_dir:
            _write_rule(rules_dir, "match.yml", MATCH_ANYTHING)  # all-modules keyword rule
            call_count = {"n": 0}
            real_compiled = mod.CompiledRule

            def counting_compiled(rule):
                call_count["n"] += 1
                return real_compiled(rule)

            case = next(iter(self.sd.cases().values()))
            a = SigmascanAnalyser(self.sd.config, case=case)
            if not a.is_compatible():
                self.skipTest("incompatible")

            # Return no events per module so the test does not actually scan large sources;
            # we only care about how many times a rule is compiled.
            with (
                patch.dict(os.environ, {"SYSDIAGNOSE_SIGMA_RULES_PATH": rules_dir}),
                patch.object(mod, "CompiledRule", side_effect=counting_compiled),
                patch.object(a, "_load_module_events", return_value=[]),
            ):
                result = a.execute()

            # The all-modules rule is scanned against many modules, but compiled exactly once.
            self.assertEqual(call_count["n"], 1)
            self.assertEqual(result, [])


class TestBuildAlert(unittest.TestCase):
    """Pure tests over build_alert."""

    def _loaded(self):
        text = (
            "title: Example rule\n"
            "id: 33333333-3333-4333-8333-333333333333\n"
            "status: test\n"
            "level: high\n"
            "tags:\n  - attack.execution\n"
            "logsource: {product: ios}\n"
            "detection:\n  sel: {data.x: alpha}\n  condition: sel\n"
        )
        return load_rule_from_yaml(text, "mem://example")

    def test_alert_shape(self):
        lr = self._loaded()
        event = {
            "datetime": "2026-01-01T00:00:00.000000+00:00",
            "message": "m",
            "timestamp_desc": "d",
            "module": "crashlogs",
            "data": {"x": "alpha"},
        }
        alert = build_alert(lr, event, "crashlogs")
        self.assertEqual(alert["module"], "sigmascan")
        self.assertTrue(alert["message"].startswith("ALERT: Example rule"))
        data = alert["data"]
        self.assertEqual(data["rule_id"], "33333333-3333-4333-8333-333333333333")
        self.assertEqual(data["rule_title"], "Example rule")
        self.assertEqual(data["level"], "high")
        self.assertEqual(data["status"], "test")
        self.assertEqual(data["matched_module"], "crashlogs")
        self.assertNotIn("matched_selection", data)
        # case_id is not carried (added by downstream ingestion), like other SAF modules.
        self.assertNotIn("case_id", data)
        self.assertEqual(data["tags"], ["attack.execution"])
        # full event embedded
        self.assertEqual(data["event"], event)

    def test_alert_datetime_from_event(self):
        lr = self._loaded()
        event = {"datetime": "2023-05-24T20:27:43.000000+00:00", "data": {"x": "alpha"}}
        alert = build_alert(lr, event, "crashlogs")
        self.assertEqual(alert["datetime"], "2023-05-24T20:27:43.000000+00:00")


if __name__ == "__main__":
    unittest.main()
