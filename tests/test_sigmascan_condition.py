import unittest

from sigma.rule import SigmaRule

from sysdiagnose.sigmascan.condition import ConditionEvaluationError, evaluate_rule
from sysdiagnose.sigmascan.matcher import serialize_event_values

# NOTE: Generic placeholders only — no real detection artifacts (see test_sigmascan_matcher).


def rule(detection_yaml: str) -> SigmaRule:
    """Build a SigmaRule from a detection block (with condition)."""
    return SigmaRule.from_yaml(
        f"title: t\nid: 2f1b0c9a-7d4e-4a1b-9c2d-0e1f2a3b4c5d\nlogsource: {{product: ios}}\ndetection:\n{detection_yaml}"
    )


class TestBooleanComposition(unittest.TestCase):
    def test_and_both_true(self):
        r = rule("  a: {data.x: alpha}\n  b: {data.y: beta}\n  condition: a and b\n")
        self.assertTrue(evaluate_rule(r, {"data": {"x": "alpha", "y": "beta"}}))

    def test_and_one_false(self):
        r = rule("  a: {data.x: alpha}\n  b: {data.y: beta}\n  condition: a and b\n")
        self.assertFalse(evaluate_rule(r, {"data": {"x": "alpha", "y": "other"}}))

    def test_or_one_true(self):
        r = rule("  a: {data.x: alpha}\n  b: {data.y: beta}\n  condition: a or b\n")
        self.assertTrue(evaluate_rule(r, {"data": {"x": "nope", "y": "beta"}}))

    def test_or_none_true(self):
        r = rule("  a: {data.x: alpha}\n  b: {data.y: beta}\n  condition: a or b\n")
        self.assertFalse(evaluate_rule(r, {"data": {"x": "nope", "y": "nope"}}))

    def test_not(self):
        r = rule("  a: {data.x: alpha}\n  condition: not a\n")
        self.assertTrue(evaluate_rule(r, {"data": {"x": "other"}}))
        self.assertFalse(evaluate_rule(r, {"data": {"x": "alpha"}}))

    def test_parentheses_precedence(self):
        # a and (b or c)
        r = rule("  a: {data.x: alpha}\n  b: {data.y: beta}\n  c: {data.z: gamma}\n  condition: a and (b or c)\n")
        # a true, c true -> match
        self.assertTrue(evaluate_rule(r, {"data": {"x": "alpha", "y": "no", "z": "gamma"}}))
        # a true, neither b nor c -> no match
        self.assertFalse(evaluate_rule(r, {"data": {"x": "alpha", "y": "no", "z": "no"}}))
        # a false -> no match regardless
        self.assertFalse(evaluate_rule(r, {"data": {"x": "no", "y": "beta", "z": "gamma"}}))

    def test_and_not_combo(self):
        # a and not b
        r = rule("  a: {data.x: alpha}\n  b: {data.y: beta}\n  condition: a and not b\n")
        self.assertTrue(evaluate_rule(r, {"data": {"x": "alpha", "y": "other"}}))
        self.assertFalse(evaluate_rule(r, {"data": {"x": "alpha", "y": "beta"}}))


class TestSelectionWithMultipleFields(unittest.TestCase):
    def test_selection_is_and_of_its_fields(self):
        # A single selection with two fields = AND of those fields.
        r = rule("  sel:\n    data.x: alpha\n    data.y: beta\n  condition: sel\n")
        self.assertTrue(evaluate_rule(r, {"data": {"x": "alpha", "y": "beta"}}))
        self.assertFalse(evaluate_rule(r, {"data": {"x": "alpha", "y": "other"}}))

    def test_value_list_is_or_within_field(self):
        r = rule("  sel:\n    data.x:\n      - alpha\n      - beta\n  condition: sel\n")
        self.assertTrue(evaluate_rule(r, {"data": {"x": "beta"}}))
        self.assertFalse(evaluate_rule(r, {"data": {"x": "gamma"}}))


class TestQuantifiers(unittest.TestCase):
    def test_one_of_wildcard(self):
        r = rule("  sel_a: {data.x: alpha}\n  sel_b: {data.y: beta}\n  condition: 1 of sel_*\n")
        self.assertTrue(evaluate_rule(r, {"data": {"x": "alpha", "y": "no"}}))
        self.assertTrue(evaluate_rule(r, {"data": {"x": "no", "y": "beta"}}))
        self.assertFalse(evaluate_rule(r, {"data": {"x": "no", "y": "no"}}))

    def test_all_of_wildcard(self):
        r = rule("  sel_a: {data.x: alpha}\n  sel_b: {data.y: beta}\n  condition: all of sel_*\n")
        self.assertTrue(evaluate_rule(r, {"data": {"x": "alpha", "y": "beta"}}))
        self.assertFalse(evaluate_rule(r, {"data": {"x": "alpha", "y": "no"}}))

    def test_one_of_them(self):
        r = rule("  sel_a: {data.x: alpha}\n  sel_b: {data.y: beta}\n  condition: 1 of them\n")
        self.assertTrue(evaluate_rule(r, {"data": {"x": "no", "y": "beta"}}))
        self.assertFalse(evaluate_rule(r, {"data": {"x": "no", "y": "no"}}))

    def test_all_of_them(self):
        r = rule("  sel_a: {data.x: alpha}\n  sel_b: {data.y: beta}\n  condition: all of them\n")
        self.assertTrue(evaluate_rule(r, {"data": {"x": "alpha", "y": "beta"}}))
        self.assertFalse(evaluate_rule(r, {"data": {"x": "alpha", "y": "no"}}))


class TestMultipleConditions(unittest.TestCase):
    """A `condition:` given as a YAML list = independent alternatives, OR across entries."""

    def test_list_of_conditions_is_or(self):
        r = rule("  a: {data.x: alpha}\n  b: {data.y: beta}\n  condition:\n    - a\n    - b\n")
        # first condition matches
        self.assertTrue(evaluate_rule(r, {"data": {"x": "alpha", "y": "no"}}))
        # second condition matches (would be MISSED if only [0] were evaluated)
        self.assertTrue(evaluate_rule(r, {"data": {"x": "no", "y": "beta"}}))
        # neither matches
        self.assertFalse(evaluate_rule(r, {"data": {"x": "no", "y": "no"}}))

    def test_list_of_conditions_second_entry_alone(self):
        # Regression guard for the old `[0]` bug: a rule whose ONLY satisfiable condition is
        # the second list entry must still match.
        r = rule("  a: {data.x: alpha}\n  b: {data.y: beta}\n  condition:\n    - a\n    - b\n")
        self.assertTrue(evaluate_rule(r, {"data": {"y": "beta"}}))


class TestKeywordLeaves(unittest.TestCase):
    def test_keyword_condition(self):
        r = rule("  keywords:\n    - TERM\n  condition: keywords\n")
        self.assertTrue(evaluate_rule(r, {"message": "has [TERM] here", "data": {}}))
        self.assertFalse(evaluate_rule(r, {"message": "nothing", "data": {}}))

    def test_keyword_or_over_multiple_terms(self):
        r = rule("  keywords:\n    - AAA\n    - BBB\n  condition: keywords\n")
        self.assertTrue(evaluate_rule(r, {"message": "has BBB", "data": {}}))
        self.assertFalse(evaluate_rule(r, {"message": "has CCC", "data": {}}))

    def test_keyword_combined_with_field(self):
        # keywords and sel  (mix of keyword leaf and field leaf)
        r = rule("  keywords:\n    - TERM\n  sel: {data.x: alpha}\n  condition: keywords and sel\n")
        self.assertTrue(evaluate_rule(r, {"message": "TERM", "data": {"x": "alpha"}}))
        self.assertFalse(evaluate_rule(r, {"message": "TERM", "data": {"x": "no"}}))


class TestModifiersThroughCondition(unittest.TestCase):
    """The condition leaf loses the `cased` modifier; evaluate_rule must recover it by
    mapping the leaf back to its detection item. These tests guard that correctness."""

    def test_contains_through_condition(self):
        r = rule("  sel: {data.x|contains: MID}\n  condition: sel\n")
        self.assertTrue(evaluate_rule(r, {"data": {"x": "left MID right"}}))
        self.assertFalse(evaluate_rule(r, {"data": {"x": "nope"}}))

    def test_startswith_through_condition(self):
        r = rule("  sel: {data.x|startswith: pre}\n  condition: sel\n")
        self.assertTrue(evaluate_rule(r, {"data": {"x": "pre.body"}}))
        self.assertFalse(evaluate_rule(r, {"data": {"x": "body.pre"}}))

    def test_cased_preserved_through_condition(self):
        # This is the critical case: `cased` is NOT present on the condition leaf, only on
        # the detection item. If evaluate_rule did not recover it, this would wrongly match.
        r = rule("  sel: {data.x|cased: AlPha}\n  condition: sel\n")
        self.assertFalse(evaluate_rule(r, {"data": {"x": "alpha"}}))
        self.assertTrue(evaluate_rule(r, {"data": {"x": "AlPha"}}))

    def test_default_case_insensitive_through_condition(self):
        # Without cased, matching stays case-insensitive through the condition path.
        r = rule("  sel: {data.x: AlPha}\n  condition: sel\n")
        self.assertTrue(evaluate_rule(r, {"data": {"x": "alpha"}}))

    def test_wildcard_through_condition(self):
        r = rule("  sel: {data.x: 'foo*bar'}\n  condition: sel\n")
        self.assertTrue(evaluate_rule(r, {"data": {"x": "fooXYZbar"}}))
        self.assertFalse(evaluate_rule(r, {"data": {"x": "Zfoobar"}}))


class TestMapListSelections(unittest.TestCase):
    """A list-of-maps selection nests SigmaDetection objects; the value index must recurse
    into them so leaves map back to their detection item (and its modifiers)."""

    def test_maplist_selection_is_or_of_maps(self):
        # `sel` as a list of maps = OR across the maps.
        r = rule("  sel:\n    - data.a: alpha\n    - data.b: beta\n  condition: sel\n")
        self.assertTrue(evaluate_rule(r, {"data": {"a": "alpha"}}))
        self.assertTrue(evaluate_rule(r, {"data": {"b": "beta"}}))
        self.assertFalse(evaluate_rule(r, {"data": {"a": "no", "b": "no"}}))

    def test_maplist_nested_cased_preserved(self):
        # `cased` buried in a nested (map-list) detection must still be recovered.
        r = rule("  sel:\n    - data.a|cased: AlPha\n    - data.b: beta\n  condition: sel\n")
        self.assertFalse(evaluate_rule(r, {"data": {"a": "alpha"}}))
        self.assertTrue(evaluate_rule(r, {"data": {"a": "AlPha"}}))


class TestEvaluateRulePlumbing(unittest.TestCase):
    def test_precomputed_values_text_matches_on_demand(self):
        r = rule("  keywords:\n    - TERM\n  condition: keywords\n")
        ev = {"message": "has TERM", "data": {}}
        precomputed = serialize_event_values(ev)
        self.assertEqual(
            evaluate_rule(r, ev, event_values_text=precomputed),
            evaluate_rule(r, ev),
        )

    def test_missing_field_makes_rule_no_match(self):
        r = rule("  sel: {data.lvl1.lvl2.key: VALUE}\n  condition: sel\n")
        self.assertFalse(evaluate_rule(r, {"data": {"other": "x"}}))

    def test_unsupported_node_type_raises(self):
        # An unknown node type in the tree must raise, not silently no-op.
        from sysdiagnose.sigmascan.condition import _evaluate_node

        class BogusNode:
            pass

        with self.assertRaises(ConditionEvaluationError):
            _evaluate_node(BogusNode(), {"data": {}}, {}, "")


if __name__ == "__main__":
    unittest.main()
