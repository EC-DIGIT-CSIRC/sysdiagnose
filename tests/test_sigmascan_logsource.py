import unittest

from sysdiagnose.sigmascan.loader import load_rule_from_yaml
from sysdiagnose.sigmascan.logsource import (
    build_module_index,
    discover_modules,
)
from sysdiagnose.utils.base import (
    BaseAnalyserInterface,
    BaseParserInterface,
)
from tests import SysdiagnoseTestCase

# NOTE: Generic placeholder detection content; public SAF module names are fine.

HDR = "title: {title}\nid: {uuid}\nlogsource:\n  product: ios\n"


def _all_modules_rule(title: str, uuid: str):
    text = HDR.format(title=title, uuid=uuid) + "detection:\n  keywords:\n    - TERM\n  condition: keywords\n"
    return load_rule_from_yaml(text, f"mem://{title}")


def _scoped_rule(title: str, uuid: str, modules: list[str]):
    mod_block = "".join(f"    - {m}\n" for m in modules)
    text = (
        HDR.format(title=title, uuid=uuid)
        + f"  modules:\n{mod_block}"
        + "detection:\n  sel: {data.x: alpha}\n  condition: sel\n"
    )
    return load_rule_from_yaml(text, f"mem://{title}")


class TestBuildModuleIndex(unittest.TestCase):
    """Pure tests over the inverted index (no SAF discovery)."""

    def test_scoped_rule_indexed_under_its_modules_only(self):
        r = _scoped_rule("s", "00000000-0000-4000-8000-000000000001", ["crashlogs", "logarchive"])
        index = build_module_index([r], {"crashlogs", "logarchive", "ps"})
        self.assertIn("crashlogs", index)
        self.assertIn("logarchive", index)
        self.assertNotIn("ps", index)
        self.assertEqual(index["crashlogs"], [r])

    def test_all_modules_rule_indexed_under_every_module(self):
        r = _all_modules_rule("a", "00000000-0000-4000-8000-000000000002")
        modules = {"crashlogs", "logarchive", "ps"}
        index = build_module_index([r], modules)
        self.assertEqual(set(index), modules)
        for mod in modules:
            self.assertEqual(index[mod], [r])

    def test_all_modules_plus_scoped_combined(self):
        allrule = _all_modules_rule("a", "00000000-0000-4000-8000-000000000003")
        scoped = _scoped_rule("s", "00000000-0000-4000-8000-000000000004", ["crashlogs"])
        modules = {"crashlogs", "logarchive"}
        index = build_module_index([allrule, scoped], modules)
        # crashlogs gets both the all-modules rule and the scoped rule
        self.assertCountEqual(index["crashlogs"], [allrule, scoped])
        # logarchive gets only the all-modules rule
        self.assertEqual(index["logarchive"], [allrule])

    def test_module_with_no_rules_absent_from_index(self):
        scoped = _scoped_rule("s", "00000000-0000-4000-8000-000000000005", ["crashlogs"])
        index = build_module_index([scoped], {"crashlogs", "logarchive", "ps"})
        self.assertEqual(set(index), {"crashlogs"})

    def test_empty_rules_yields_empty_index(self):
        self.assertEqual(build_module_index([], {"crashlogs", "logarchive"}), {})

    def test_scoped_rule_naming_unknown_module_skipped_defensively(self):
        # modules loaded without a known_modules set may contain an unknown name; the index
        # builder skips names not in the discovered set rather than creating a phantom entry.
        r = _scoped_rule("s", "00000000-0000-4000-8000-000000000006", ["crashlogs", "ghost"])
        index = build_module_index([r], {"crashlogs", "logarchive"})
        self.assertEqual(set(index), {"crashlogs"})


class TestModuleDiscovery(SysdiagnoseTestCase):
    """Tests that hit SAF's real parser/analyser discovery."""

    def test_discover_modules_includes_parsers_and_analysers(self):
        modules = discover_modules(self.sd.config)
        # Known parser and known analyser both present.
        self.assertIn("crashlogs", modules)
        self.assertIn("apps", modules)

    def test_discover_modules_excludes_self(self):
        # sigmascan sets scannable=False, so it drops out of the scannable set (no name
        # special-case needed) — it must never scan its own output.
        modules = discover_modules(self.sd.config)
        self.assertNotIn("sigmascan", modules)

    def test_discover_modules_excludes_other_scanners(self):
        # yarascan is a scanner (scannable=False); its findings are not a data source.
        modules = discover_modules(self.sd.config)
        self.assertNotIn("yarascan", modules)

    def test_discover_modules_includes_json_format(self):
        # apps is a json-format analyser -> scannable.
        modules = discover_modules(self.sd.config)
        self.assertIn("apps", modules)

    def test_discover_modules_excludes_non_event_formats(self):
        # Text/custom/binary-format modules are not event streams and must be excluded from
        # the scannable set (and thus from logsource.modules validation).
        modules = discover_modules(self.sd.config)
        for name in ("ps_matrix", "coverage", "wifi_geolocation", "wifi_geolocation_kml", "mcstateshared"):
            cls = self.sd.config.get_module_class(name)
            if cls is None:
                continue  # module not present in this build
            if getattr(cls, "format", None) in ("jsonl", "json"):
                continue  # format changed; not the case under test
            self.assertNotIn(name, modules, f"{name} is non-event format and must be excluded")

    def test_get_module_class_resolves_parser(self):
        cls = self.sd.config.get_module_class("crashlogs")
        self.assertIsNotNone(cls)
        self.assertTrue(issubclass(cls, BaseParserInterface))

    def test_get_module_class_resolves_analyser(self):
        cls = self.sd.config.get_module_class("apps")
        self.assertIsNotNone(cls)
        self.assertTrue(issubclass(cls, BaseAnalyserInterface))

    def test_get_module_class_parser_precedence(self):
        # A name that is a known parser resolves to a parser class (parser-first).
        cls = self.sd.config.get_module_class("crashlogs")
        self.assertTrue(issubclass(cls, BaseParserInterface))
        self.assertFalse(issubclass(cls, BaseAnalyserInterface))

    def test_get_module_class_unknown_returns_none(self):
        self.assertIsNone(self.sd.config.get_module_class("no_such_module"))

    def test_discovered_modules_usable_as_known_modules(self):
        # The discovered set is what the loader validates logsource.modules against:
        # a rule scoped to a real module keeps that module when validated against it.
        modules = discover_modules(self.sd.config)
        reloaded = load_rule_from_yaml(
            HDR.format(title="s2", uuid="00000000-0000-4000-8000-000000000008")
            + "  modules:\n    - crashlogs\n"
            + "detection:\n  sel: {data.x: alpha}\n  condition: sel\n",
            "mem://s2",
            known_modules=modules,
        )
        self.assertEqual(reloaded.modules, ("crashlogs",))


if __name__ == "__main__":
    unittest.main()
