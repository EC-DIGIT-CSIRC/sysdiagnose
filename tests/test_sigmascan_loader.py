import os
import tempfile
import unittest

from sysdiagnose.sigmascan.loader import (
    ALLOWED_MODIFIERS,
    DEFAULT_RULES_PATH,
    RULES_PATH_ENV_VAR,
    LoadedRule,
    RuleValidationError,
    discover_rule_files,
    extract_modules,
    get_rules_path,
    load_rule_from_yaml,
    load_rules,
)

# NOTE: These fixtures exercise rule loading/validation mechanics only. Detection content
# (field paths, values, keyword terms) uses neutral placeholders and must NOT reference real
# detection artifacts. Public SAF *module* names (crashlogs, logarchive) are fine — they are
# the real names the loader resolves against.

# ---- rule fixtures -----------------------------------------------------------------

VALID_ALL_MODULES = """
title: All-modules keyword rule
id: 2f1b0c9a-7d4e-4a1b-9c2d-0e1f2a3b4c5d
status: experimental
level: critical
logsource:
  product: ios
detection:
  keywords:
    - TERM_ALPHA
    - TERM_BETA
  condition: keywords
"""

VALID_MODULE_SCOPED = """
title: Module-scoped field rule
id: 8c7d1e2f-3a4b-4c6d-8e8f-9a0b1c2d3e4f
status: test
level: high
logsource:
  product: ios
  modules:
    - crashlogs
    - logarchive
detection:
  sel_a:
    data.name:
      - alpha
      - beta
  sel_b:
    data.lvl1.lvl2.key|contains: MIDDLE
  condition: sel_a and sel_b
"""

BAD_UUID = """
title: Bad uuid
id: not-a-uuid
logsource:
  product: ios
detection:
  sel:
    data.x: y
  condition: sel
"""

NO_LOGSOURCE = """
title: No logsource
id: 11111111-2222-3333-4444-555555555555
detection:
  sel:
    data.x: y
  condition: sel
"""

NO_DETECTION = """
title: No detection
id: 22222222-3333-4444-5555-666666666666
logsource:
  product: ios
"""

UNSUPPORTED_REGEX = """
title: Uses regex
id: 33333333-4444-5555-6666-777777777777
logsource:
  product: ios
detection:
  sel:
    data.field|re: '.*pattern.*'
  condition: sel
"""

UNSUPPORTED_BASE64 = """
title: Uses base64
id: aaaaaaaa-1111-2222-3333-444444444444
logsource:
  product: ios
detection:
  sel:
    data.field|base64: value
  condition: sel
"""

UNSUPPORTED_CIDR = """
title: Uses cidr
id: bbbbbbbb-1111-2222-3333-444444444444
logsource:
  product: ios
detection:
  sel:
    data.field|cidr: 10.0.0.0/8
  condition: sel
"""

# A chain of one allowed modifier (cased) and one unsupported (re) -> whole rule rejected.
CHAINED_ALLOWED_AND_UNSUPPORTED = """
title: Chained cased and regex
id: cccccccc-1111-2222-3333-444444444444
logsource:
  product: ios
detection:
  sel:
    data.field|cased|re: '.*pattern.*'
  condition: sel
"""

# `modules` present but a bare string, not a list.
MODULES_NOT_A_LIST = """
title: Modules not a list
id: dddddddd-1111-2222-3333-444444444444
logsource:
  product: ios
  modules: crashlogs
detection:
  sel:
    data.x: y
  condition: sel
"""

# `modules` list with a non-string entry.
MODULES_NON_STRING_ENTRY = """
title: Modules non-string entry
id: eeeeeeee-1111-2222-3333-444444444444
logsource:
  product: ios
  modules:
    - crashlogs
    - 123
detection:
  sel:
    data.x: y
  condition: sel
"""

# A list-of-maps selection (nested SigmaDetection) with an unsupported modifier buried in
# the second map. The allow-list must recurse into the nested detection and reject it.
MAPLIST_NESTED_UNSUPPORTED = """
title: Map-list nested unsupported modifier
id: 10101010-2020-3030-4040-505050505050
logsource:
  product: ios
detection:
  sel:
    - data.a: alpha
    - data.b|re: '.*'
  condition: sel
"""

# A valid list-of-maps selection (nested detections, all supported modifiers).
MAPLIST_VALID = """
title: Map-list valid
id: 20202020-3030-4040-5050-606060606060
logsource:
  product: ios
detection:
  sel:
    - data.a: alpha
    - data.b|contains: beta
  condition: sel
"""

# A condition referencing a selection that does not exist -> must be rejected at load.
BAD_CONDITION_UNDEFINED_SELECTION = """
title: Condition references undefined selection
id: 30303030-4040-5050-6060-707070707070
logsource:
  product: ios
detection:
  sel:
    data.x: alpha
  condition: nonexistent
"""

# `modules` list with the same name twice -> de-duplicated on load.
MODULES_DUPLICATE_ENTRY = """
title: Duplicate module entries
id: ffffffff-1111-2222-3333-444444444444
logsource:
  product: ios
  modules:
    - crashlogs
    - crashlogs
    - logarchive
detection:
  sel:
    data.x: y
  condition: sel
"""

UNKNOWN_MODULE = """
title: Unknown module
id: 44444444-5555-6666-7777-888888888888
logsource:
  product: ios
  modules:
    - no_such_module
detection:
  sel:
    data.x: y
  condition: sel
"""

# A rule listing one KNOWN and one UNKNOWN module. The unknown entry is dropped and logged
# (logged loudly), while the rule is KEPT for its known module(s).
MIXED_KNOWN_AND_UNKNOWN_MODULES = """
title: Mixed known and unknown modules
id: 77777777-8888-9999-aaaa-bbbbbbbbbbbb
logsource:
  product: ios
  modules:
    - crashlogs
    - no_such_module
detection:
  sel:
    data.x: y
  condition: sel
"""


def _write(dir_path: str, name: str, text: str) -> str:
    path = os.path.join(dir_path, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)
    return path


class TestSigmascanLoaderUnit(unittest.TestCase):
    """Pure unit tests over load_rule_from_yaml / extract_modules (no filesystem)."""

    def test_valid_all_modules_rule_parses(self):
        lr = load_rule_from_yaml(VALID_ALL_MODULES, "mem://all")
        self.assertIsInstance(lr, LoadedRule)
        self.assertIsNone(lr.modules, "all-modules rule should have modules=None")
        self.assertTrue(lr.is_all_modules)
        self.assertEqual(lr.id, "2f1b0c9a-7d4e-4a1b-9c2d-0e1f2a3b4c5d")
        self.assertEqual(lr.title, "All-modules keyword rule")

    def test_valid_module_scoped_rule_extracts_modules(self):
        lr = load_rule_from_yaml(VALID_MODULE_SCOPED, "mem://scoped")
        self.assertEqual(lr.modules, ("crashlogs", "logarchive"))
        self.assertFalse(lr.is_all_modules)

    def test_extract_modules_all_modules_is_none(self):
        lr = load_rule_from_yaml(VALID_ALL_MODULES, "mem://all")
        self.assertIsNone(extract_modules(lr.rule))

    def test_bad_uuid_raises(self):
        from sigma.exceptions import SigmaError

        with self.assertRaises(SigmaError):
            load_rule_from_yaml(BAD_UUID, "mem://baduuid")

    def test_missing_logsource_raises(self):
        from sigma.exceptions import SigmaError

        with self.assertRaises(SigmaError):
            load_rule_from_yaml(NO_LOGSOURCE, "mem://nologsource")

    def test_missing_detection_raises(self):
        from sigma.exceptions import SigmaError

        with self.assertRaises(SigmaError):
            load_rule_from_yaml(NO_DETECTION, "mem://nodetection")

    def test_unsupported_modifier_rejected(self):
        with self.assertRaises(RuleValidationError) as ctx:
            load_rule_from_yaml(UNSUPPORTED_REGEX, "mem://regex")
        self.assertIn("unsupported modifier", str(ctx.exception).lower())

    def test_unsupported_base64_rejected(self):
        with self.assertRaises(RuleValidationError) as ctx:
            load_rule_from_yaml(UNSUPPORTED_BASE64, "mem://base64")
        self.assertIn("unsupported modifier", str(ctx.exception).lower())

    def test_unsupported_cidr_rejected(self):
        with self.assertRaises(RuleValidationError) as ctx:
            load_rule_from_yaml(UNSUPPORTED_CIDR, "mem://cidr")
        self.assertIn("unsupported modifier", str(ctx.exception).lower())

    def test_chained_allowed_and_unsupported_modifier_rejected(self):
        # A chain mixing an allowed modifier (cased) with an unsupported one (re) is
        # rejected as a whole. Depending on the chain, rejection may come from pySigma at
        # parse time (SigmaError) or from our allow-list (RuleValidationError); either way
        # the rule does not load.
        from sigma.exceptions import SigmaError

        with self.assertRaises((RuleValidationError, SigmaError)):
            load_rule_from_yaml(CHAINED_ALLOWED_AND_UNSUPPORTED, "mem://chained")

    def test_allowed_modifiers_accepted(self):
        for mod in ("contains", "startswith", "endswith", "cased"):
            text = f"""
title: Modifier {mod}
id: 55555555-6666-7777-8888-99999999999a
logsource:
  product: ios
detection:
  sel:
    data.field|{mod}: value
  condition: sel
"""
            lr = load_rule_from_yaml(text, f"mem://{mod}")
            self.assertIsInstance(lr, LoadedRule)

    def test_unknown_module_rejected_when_known_set_supplied(self):
        with self.assertRaises(RuleValidationError) as ctx:
            load_rule_from_yaml(UNKNOWN_MODULE, "mem://unknown", known_modules={"crashlogs", "logarchive"})
        self.assertIn("unknown module", str(ctx.exception).lower())

    def test_known_module_accepted_when_known_set_supplied(self):
        lr = load_rule_from_yaml(VALID_MODULE_SCOPED, "mem://scoped", known_modules={"crashlogs", "logarchive", "ps"})
        self.assertEqual(lr.modules, ("crashlogs", "logarchive"))

    def test_unknown_module_deferred_when_no_known_set(self):
        # Without a discovery context, the unknown-module check is deferred (parses fine).
        lr = load_rule_from_yaml(UNKNOWN_MODULE, "mem://unknown")
        self.assertEqual(lr.modules, ("no_such_module",))

    def test_mixed_known_and_unknown_modules_keeps_known_and_logs(self):
        # One known + one unknown module -> the rule is KEPT for the known module, the
        # unknown one is dropped, and an error is logged naming the unknown module. This
        # preserves the detection potential of the valid part while still failing loud.
        with self.assertLogs("sysdiagnose", level="ERROR") as cm:
            lr = load_rule_from_yaml(
                MIXED_KNOWN_AND_UNKNOWN_MODULES,
                "mem://mixed",
                known_modules={"crashlogs", "logarchive"},
            )
        # Rule survives, scoped to only the known module.
        self.assertIsInstance(lr, LoadedRule)
        self.assertEqual(lr.modules, ("crashlogs",))
        # The error names ONLY the dropped unknown module. It must NOT name the kept known
        # module, so the log is unambiguously about the failure (no_such_module) alone.
        joined = "\n".join(cm.output)
        self.assertIn("no_such_module", joined)
        self.assertNotIn("crashlogs", joined)

    def test_all_unknown_modules_rejects_whole_rule(self):
        # If EVERY listed module is unknown there is nothing to scan -> reject the rule.
        with self.assertRaises(RuleValidationError) as ctx:
            load_rule_from_yaml(UNKNOWN_MODULE, "mem://allunknown", known_modules={"crashlogs", "logarchive"})
        self.assertIn("no_such_module", str(ctx.exception))

    def test_modules_not_a_list_rejected(self):
        with self.assertRaises(RuleValidationError) as ctx:
            load_rule_from_yaml(MODULES_NOT_A_LIST, "mem://notalist")
        self.assertIn("list", str(ctx.exception).lower())

    def test_modules_non_string_entry_rejected(self):
        with self.assertRaises(RuleValidationError) as ctx:
            load_rule_from_yaml(MODULES_NON_STRING_ENTRY, "mem://nonstring")
        self.assertIn("non-empty string", str(ctx.exception).lower())

    def test_modules_duplicate_entries_deduped(self):
        lr = load_rule_from_yaml(MODULES_DUPLICATE_ENTRY, "mem://dupe")
        # crashlogs appears twice in the source -> collapsed to one, order preserved.
        self.assertEqual(lr.modules, ("crashlogs", "logarchive"))

    def test_empty_modules_list_rejected(self):
        text = """
title: Empty modules
id: 66666666-7777-8888-9999-aaaaaaaaaaaa
logsource:
  product: ios
  modules: []
detection:
  sel:
    data.x: y
  condition: sel
"""
        with self.assertRaises(RuleValidationError):
            load_rule_from_yaml(text, "mem://emptymodules")

    def test_allow_list_constant(self):
        # Exactly the four v1-permitted modifier classes.
        self.assertEqual(len(ALLOWED_MODIFIERS), 4)

    def test_maplist_nested_unsupported_modifier_rejected(self):
        # A list-of-maps selection nests SigmaDetection objects; the allow-list must recurse
        # into them (not crash, not silently bypass) and reject an unsupported modifier.
        with self.assertRaises(RuleValidationError) as ctx:
            load_rule_from_yaml(MAPLIST_NESTED_UNSUPPORTED, "mem://maplist-bad")
        self.assertIn("unsupported modifier", str(ctx.exception).lower())

    def test_maplist_valid_loads(self):
        lr = load_rule_from_yaml(MAPLIST_VALID, "mem://maplist-ok")
        self.assertIsInstance(lr, LoadedRule)

    def test_condition_referencing_undefined_selection_rejected(self):
        # A broken condition must be caught at LOAD time (parsed eagerly), not deferred to
        # scan time. pySigma raises a SigmaConditionError (a SigmaError) on parse.
        from sigma.exceptions import SigmaError

        with self.assertRaises(SigmaError):
            load_rule_from_yaml(BAD_CONDITION_UNDEFINED_SELECTION, "mem://badcond")


class TestSigmascanLoaderFilesystem(unittest.TestCase):
    """Tests over the directory-discovery + fail-soft load path."""

    def test_get_rules_path_default_and_env(self):
        # Default
        saved = os.environ.pop(RULES_PATH_ENV_VAR, None)
        try:
            self.assertEqual(get_rules_path(), DEFAULT_RULES_PATH)
            os.environ[RULES_PATH_ENV_VAR] = "/tmp/custom_sigma"
            self.assertEqual(get_rules_path(), "/tmp/custom_sigma")
        finally:
            os.environ.pop(RULES_PATH_ENV_VAR, None)
            if saved is not None:
                os.environ[RULES_PATH_ENV_VAR] = saved

    def test_discover_rule_files_recursive_yml_and_yaml(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "a.yml", VALID_ALL_MODULES)
            _write(d, "sub/b.yaml", VALID_MODULE_SCOPED)
            _write(d, "notes.txt", "ignored")
            _write(d, "sub/deep/c.yml", VALID_ALL_MODULES)
            found = discover_rule_files(d)
            self.assertEqual(len(found), 3)
            self.assertTrue(all(f.endswith((".yml", ".yaml")) for f in found))

    def test_missing_directory_returns_empty(self):
        self.assertEqual(load_rules("/nonexistent/path/to/sigma"), [])

    def test_malformed_yaml_file_skipped_not_crash(self):
        # A syntactically broken YAML file must be skipped (logged), not crash the run.
        malformed = "title: x\n  bad: : indent: broken\n :\n"
        with tempfile.TemporaryDirectory() as d:
            _write(d, "broken.yml", malformed)
            _write(d, "good.yml", VALID_ALL_MODULES)
            with self.assertLogs("sysdiagnose", level="ERROR") as cm:
                loaded = load_rules(d)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].title, "All-modules keyword rule")
            self.assertIn("broken.yml", "\n".join(cm.output))

    def test_unreadable_file_skipped_not_crash(self):
        # A rule file that cannot be read (permission denied) is skipped, not fatal.
        with tempfile.TemporaryDirectory() as d:
            bad_path = _write(d, "noperm.yml", VALID_ALL_MODULES)
            _write(d, "good.yml", VALID_MODULE_SCOPED)
            os.chmod(bad_path, 0o000)
            try:
                # Skip if running as root, where chmod 000 does not prevent reads.
                if os.access(bad_path, os.R_OK):
                    self.skipTest("cannot make file unreadable (likely running as root)")
                with self.assertLogs("sysdiagnose", level="ERROR") as cm:
                    loaded = load_rules(d)
                self.assertEqual(len(loaded), 1)
                self.assertEqual(loaded[0].title, "Module-scoped field rule")
                self.assertIn("noperm.yml", "\n".join(cm.output))
            finally:
                os.chmod(bad_path, 0o644)

    def test_empty_directory_logs_error(self):
        # A directory that exists but has no rule files -> nothing loads -> WARNING (a
        # configuration state, not an execution error — SAF would otherwise mark the whole
        # analyser run as ERROR).
        with tempfile.TemporaryDirectory() as d:
            _write(d, "notes.txt", "not a rule")
            with self.assertLogs("sysdiagnose", level="WARNING") as cm:
                loaded = load_rules(d)
            self.assertEqual(loaded, [])
            self.assertIn("No valid sigmascan rules", "\n".join(cm.output))

    def test_all_invalid_rules_logs_each_and_warns_no_rules(self):
        # Every file is invalid -> each bad rule logs an ERROR (per-rule authoring fault),
        # and the empty result additionally triggers the "no rules loaded" WARNING.
        with tempfile.TemporaryDirectory() as d:
            _write(d, "bad_uuid.yml", BAD_UUID)
            _write(d, "regex.yml", UNSUPPORTED_REGEX)
            with self.assertLogs("sysdiagnose", level="WARNING") as cm:
                loaded = load_rules(d)
            self.assertEqual(loaded, [])
            joined = "\n".join(cm.output)
            # Per-rule ERRORs still fire (captured because WARNING includes ERROR).
            self.assertIn("bad_uuid.yml", joined)
            self.assertIn("regex.yml", joined)
            # Plus the no-rules WARNING.
            self.assertIn("No valid sigmascan rules", joined)

    def test_duplicate_rule_ids_warn(self):
        # Two rules with the same id load fine but trigger a warning naming the id.
        dup_a = VALID_ALL_MODULES  # id 2f1b0c9a-...
        dup_b = VALID_ALL_MODULES.replace("All-modules keyword rule", "Duplicate id twin")  # same id, different title
        with tempfile.TemporaryDirectory() as d:
            _write(d, "a.yml", dup_a)
            _write(d, "b.yml", dup_b)
            with self.assertLogs("sysdiagnose", level="WARNING") as cm:
                loaded = load_rules(d)
            # Both still load (id is not used as a key).
            self.assertEqual(len(loaded), 2)
            joined = "\n".join(cm.output)
            self.assertIn("duplicate sigmascan rule id", joined.lower())
            self.assertIn("2f1b0c9a-7d4e-4a1b-9c2d-0e1f2a3b4c5d", joined)

    def test_load_rules_skips_invalid_and_loads_valid(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "good_all.yml", VALID_ALL_MODULES)
            _write(d, "good_scoped.yml", VALID_MODULE_SCOPED)
            _write(d, "bad_uuid.yml", BAD_UUID)
            _write(d, "no_logsource.yml", NO_LOGSOURCE)
            _write(d, "no_detection.yml", NO_DETECTION)
            _write(d, "regex.yml", UNSUPPORTED_REGEX)

            with self.assertLogs("sysdiagnose", level="ERROR") as cm:
                loaded = load_rules(d)

            # Two valid rules loaded; four invalid skipped.
            self.assertEqual(len(loaded), 2)
            titles = sorted(lr.title for lr in loaded)
            self.assertEqual(titles, ["All-modules keyword rule", "Module-scoped field rule"])

            # Each bad rule produced an error log naming its file.
            joined = "\n".join(cm.output)
            for bad in ("bad_uuid.yml", "no_logsource.yml", "no_detection.yml", "regex.yml"):
                self.assertIn(bad, joined)

    def test_load_rules_unknown_module_skipped_with_known_set(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "unknown.yml", UNKNOWN_MODULE)
            _write(d, "good.yml", VALID_ALL_MODULES)
            with self.assertLogs("sysdiagnose", level="ERROR") as cm:
                loaded = load_rules(d, known_modules={"crashlogs", "logarchive"})
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].title, "All-modules keyword rule")
            self.assertIn("unknown.yml", "\n".join(cm.output))

    def test_load_rules_all_unknown_modules_skipped_and_run_continues(self):
        # When EVERY module of a rule is unknown, load_rules (the app entry point) catches
        # the RuleValidationError, logs it naming the file + unknown module, SKIPS that one
        # rule, and CONTINUES loading the rest. The app does not stop.
        with tempfile.TemporaryDirectory() as d:
            _write(d, "all_unknown.yml", UNKNOWN_MODULE)  # modules: [no_such_module]
            _write(d, "good.yml", VALID_ALL_MODULES)
            with self.assertLogs("sysdiagnose", level="ERROR") as cm:
                loaded = load_rules(d, known_modules={"crashlogs", "logarchive"})
            # The valid rule still loaded; the all-unknown rule was dropped.
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].title, "All-modules keyword rule")
            self.assertNotIn("Unknown module", [lr.title for lr in loaded])
            # Error names the offending file and the unknown module.
            joined = "\n".join(cm.output)
            self.assertIn("all_unknown.yml", joined)
            self.assertIn("no_such_module", joined)

    def test_load_rules_mixed_modules_rule_kept_for_known_module(self):
        # A rule mixing a known and an unknown module is KEPT (scoped to the known module),
        # the unknown module is dropped and logged, and the unrelated valid rule also loads.
        with tempfile.TemporaryDirectory() as d:
            _write(d, "mixed.yml", MIXED_KNOWN_AND_UNKNOWN_MODULES)
            _write(d, "good.yml", VALID_ALL_MODULES)
            with self.assertLogs("sysdiagnose", level="ERROR") as cm:
                loaded = load_rules(d, known_modules={"crashlogs", "logarchive"})
            self.assertEqual(len(loaded), 2)
            by_title = {lr.title: lr for lr in loaded}
            self.assertIn("Mixed known and unknown modules", by_title)
            self.assertEqual(by_title["Mixed known and unknown modules"].modules, ("crashlogs",))
            joined = "\n".join(cm.output)
            self.assertIn("mixed.yml", joined)
            self.assertIn("no_such_module", joined)
            # The log names only the dropped module, not the kept one.
            self.assertNotIn("crashlogs", joined)

    def test_load_rules_run_continues_after_each_bad_class(self):
        # The run must not abort on any single bad rule — all valid rules still load.
        with tempfile.TemporaryDirectory() as d:
            _write(d, "01_bad_uuid.yml", BAD_UUID)
            _write(d, "02_good.yml", VALID_ALL_MODULES)
            _write(d, "03_regex.yml", UNSUPPORTED_REGEX)
            _write(d, "04_good2.yml", VALID_MODULE_SCOPED)
            with self.assertLogs("sysdiagnose", level="ERROR"):
                loaded = load_rules(d)
            self.assertEqual(len(loaded), 2)


if __name__ == "__main__":
    unittest.main()
