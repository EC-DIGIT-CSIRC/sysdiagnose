import unittest

from sysdiagnose.utils.base import BaseParserInterface
from sysdiagnose.utils.summary import ExecutionStatus
from tests import SysdiagnoseTestCase


class TestIsCompatibleMethod(unittest.TestCase):
    """Unit tests for BaseInterface.is_compatible() logic without requiring case data."""

    def _make_parser_class(self, ios_version_spec):
        """Helper to create a minimal parser class with a given ios_version spec."""

        class FakeParser(BaseParserInterface):
            description = "Fake parser for testing"
            ios_version = ios_version_spec
            format = "jsonl"

            def __init__(self):
                # Bypass BaseInterface.__init__ — we only test is_compatible()
                self.module_name = "fake_parser"

            def get_log_files(self):
                return []

            def execute(self):
                return []

        return FakeParser()

    # --- Wildcard (default) ---

    def test_wildcard_is_always_compatible(self):
        p = self._make_parser_class("*")
        self.assertTrue(p.is_compatible("14.0"))
        self.assertTrue(p.is_compatible("17.0"))
        self.assertTrue(p.is_compatible("99.9.9"))

    # --- Greater than or equal ---

    def test_gte_compatible(self):
        p = self._make_parser_class(">=17.0")
        self.assertTrue(p.is_compatible("17.0"))
        self.assertTrue(p.is_compatible("17.1"))
        self.assertTrue(p.is_compatible("18.0"))

    def test_gte_incompatible(self):
        p = self._make_parser_class(">=17.0")
        self.assertFalse(p.is_compatible("16.9.9"))
        self.assertFalse(p.is_compatible("16.0"))
        self.assertFalse(p.is_compatible("14.4.1"))

    # --- Less than ---

    def test_lt_compatible(self):
        p = self._make_parser_class("<17.0")
        self.assertTrue(p.is_compatible("16.9.9"))
        self.assertTrue(p.is_compatible("14.0"))

    def test_lt_incompatible(self):
        p = self._make_parser_class("<17.0")
        self.assertFalse(p.is_compatible("17.0"))
        self.assertFalse(p.is_compatible("18.0"))

    # --- Range (AND semantics with comma) ---

    def test_range_compatible(self):
        p = self._make_parser_class(">=14.0,<17.0")
        self.assertTrue(p.is_compatible("14.0"))
        self.assertTrue(p.is_compatible("15.7.6"))
        self.assertTrue(p.is_compatible("16.9.9"))

    def test_range_incompatible_below(self):
        p = self._make_parser_class(">=14.0,<17.0")
        self.assertFalse(p.is_compatible("13.9"))

    def test_range_incompatible_above(self):
        p = self._make_parser_class(">=14.0,<17.0")
        self.assertFalse(p.is_compatible("17.0"))
        self.assertFalse(p.is_compatible("18.0"))

    # --- Exact version ---

    def test_exact_compatible(self):
        p = self._make_parser_class("==16.3.1")
        self.assertTrue(p.is_compatible("16.3.1"))

    def test_exact_incompatible(self):
        p = self._make_parser_class("==16.3.1")
        self.assertFalse(p.is_compatible("16.3.0"))
        self.assertFalse(p.is_compatible("16.4"))

    # --- Wildcard match (PEP 440 ==X.*) ---

    def test_wildcard_minor_compatible(self):
        p = self._make_parser_class("==16.*")
        self.assertTrue(p.is_compatible("16.0"))
        self.assertTrue(p.is_compatible("16.3.1"))
        self.assertTrue(p.is_compatible("16.9.9"))

    def test_wildcard_minor_incompatible(self):
        p = self._make_parser_class("==16.*")
        self.assertFalse(p.is_compatible("15.9.9"))
        self.assertFalse(p.is_compatible("17.0"))

    # --- Not equal ---

    def test_not_equal_compatible(self):
        p = self._make_parser_class("!=16.0")
        self.assertTrue(p.is_compatible("15.0"))
        self.assertTrue(p.is_compatible("16.1"))
        self.assertTrue(p.is_compatible("17.0"))

    def test_not_equal_incompatible(self):
        p = self._make_parser_class("!=16.0")
        self.assertFalse(p.is_compatible("16.0"))

    # --- None ios_version_str (unknown version) ---

    def test_none_version_assumes_compatible(self):
        p = self._make_parser_class(">=17.0")
        # Override case_ios_version to simulate unknown version
        type(p).case_ios_version = property(lambda self: None)
        self.assertTrue(p.is_compatible(None))

    # --- Invalid specifier raises error ---

    def test_invalid_specifier_raises_error(self):
        p = self._make_parser_class("not_a_valid_spec")
        from packaging.specifiers import InvalidSpecifier

        with self.assertRaises(InvalidSpecifier):
            p.is_compatible("17.0")

    # --- Invalid version string degrades gracefully ---

    def test_invalid_version_string_assumes_compatible(self):
        p = self._make_parser_class(">=17.0")
        self.assertTrue(p.is_compatible("not_a_version"))


class TestVersionCompatibilitySkipIntegration(SysdiagnoseTestCase):
    """Integration test: verify that incompatible parsers produce SKIPPED summaries."""

    def test_incompatible_parser_is_skipped(self):
        """A parser with ios_version='>=99.0' should be skipped for all real test cases."""
        case_id = self.sd.get_case_ids()[0]
        case = self.sd.cases()[case_id]

        # Monkey-patch DemoParser to require an impossibly high iOS version
        from sysdiagnose.parsers.demo_parser import DemoParser

        original_ios_version = DemoParser.ios_version
        try:
            DemoParser.ios_version = ">=99.0"

            parser = DemoParser(self.sd.config, case=case)
            parser.save_result(force=True)

            summary = parser.get_result_summary()
            self.assertEqual(summary.status, ExecutionStatus.SKIPPED)
            self.assertEqual(summary.num_events, 0)
            self.assertIsNone(summary.start_time)
            self.assertIsNone(summary.duration)

            result = parser.get_result()
            self.assertEqual(result, [])
        finally:
            DemoParser.ios_version = original_ios_version

    def test_compatible_parser_executes_normally(self):
        """A parser with ios_version='*' should execute normally."""
        case_id = self.sd.get_case_ids()[0]
        case = self.sd.cases()[case_id]

        from sysdiagnose.parsers.demo_parser import DemoParser

        parser = DemoParser(self.sd.config, case=case)
        self.assertEqual(parser.ios_version, "*")

        parser.save_result(force=True)

        summary = parser.get_result_summary()
        self.assertNotEqual(summary.status, ExecutionStatus.SKIPPED)
        self.assertEqual(summary.num_events, 1)

    def test_compatible_parser_with_matching_version(self):
        """A parser with a version range that includes the case iOS version should execute."""
        case_id = self.sd.get_case_ids()[0]
        case = self.sd.cases()[case_id]

        from sysdiagnose.parsers.demo_parser import DemoParser

        original_ios_version = DemoParser.ios_version
        try:
            # Set to a range that includes all known iOS versions in test data
            DemoParser.ios_version = ">=10.0"

            parser = DemoParser(self.sd.config, case=case)
            parser.save_result(force=True)

            summary = parser.get_result_summary()
            self.assertNotEqual(summary.status, ExecutionStatus.SKIPPED)
            self.assertGreater(summary.num_events, 0)
        finally:
            DemoParser.ios_version = original_ios_version


if __name__ == "__main__":
    unittest.main()
