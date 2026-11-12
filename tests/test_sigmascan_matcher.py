import unittest

from sigma.rule import SigmaRule

from sysdiagnose.sigmascan.matcher import (
    collect_values,
    match_detection_item,
    resolve_field,
    serialize_event_values,
)

# NOTE: These tests exercise matching *mechanics* only. They deliberately use neutral
# placeholder fields (data.field, data.lvl1.lvl2.key, ...) and placeholder values
# (alpha, VALUE, foo*bar, ...). They must NOT reference real detection artifacts
# (process names, field paths, indicator strings) — those belong with the rules, not here.


def detection_item(detection_yaml: str, selection: str = "sel"):
    """Parse a rule and return the first detection item of the named selection."""
    rule = SigmaRule.from_yaml(
        "title: t\n"
        "id: 2f1b0c9a-7d4e-4a1b-9c2d-0e1f2a3b4c5d\n"
        "logsource: {product: ios}\n"
        "detection:\n"
        f"{detection_yaml}"
        f"  condition: {selection}\n"
    )
    return rule.detection.detections[selection].detection_items[0]


def all_items(detection_yaml: str, selection: str = "sel"):
    """Parse a rule and return all detection items of the named selection."""
    rule = SigmaRule.from_yaml(
        "title: t\n"
        "id: 2f1b0c9a-7d4e-4a1b-9c2d-0e1f2a3b4c5d\n"
        "logsource: {product: ios}\n"
        "detection:\n"
        f"{detection_yaml}"
        f"  condition: {selection}\n"
    )
    return rule.detection.detections[selection].detection_items


# ---- field resolution --------------------------------------------------------------


class TestResolveField(unittest.TestCase):
    def test_top_level(self):
        ev = {"message": "hello", "module": "module_a"}
        self.assertEqual(resolve_field(ev, "message"), "hello")

    def test_top_level_field_match_via_public_api(self):
        # A rule can target a top-level field (message/module/...) through match_detection_item.
        item = detection_item("  sel: {module: module_a}\n")
        self.assertTrue(match_detection_item(item, {"module": "module_a", "data": {}}))
        self.assertFalse(match_detection_item(item, {"module": "module_b", "data": {}}))

    def test_nested(self):
        ev = {"data": {"lvl1": {"lvl2": {"key": "VALUE"}}}}
        self.assertEqual(resolve_field(ev, "data.lvl1.lvl2.key"), "VALUE")

    def test_missing_intermediate(self):
        from sysdiagnose.sigmascan.matcher import _MISSING

        ev = {"data": {"name": "alpha"}}
        self.assertIs(resolve_field(ev, "data.lvl1.lvl2.key"), _MISSING)

    def test_intermediate_not_dict(self):
        from sysdiagnose.sigmascan.matcher import _MISSING

        ev = {"data": "not-a-dict"}
        self.assertIs(resolve_field(ev, "data.name"), _MISSING)


# ---- operators ---------------------------------------------------------------------


class TestOperators(unittest.TestCase):
    def test_exact_match(self):
        item = detection_item("  sel: {data.name: alpha}\n")
        self.assertTrue(match_detection_item(item, {"data": {"name": "alpha"}}))
        self.assertFalse(match_detection_item(item, {"data": {"name": "beta"}}))

    def test_exact_is_full_value_not_substring(self):
        item = detection_item("  sel: {data.name: alph}\n")
        self.assertFalse(match_detection_item(item, {"data": {"name": "alpha"}}))

    def test_value_list_equals_any_of(self):
        item = detection_item("  sel:\n    data.name:\n      - alpha\n      - beta\n")
        self.assertTrue(match_detection_item(item, {"data": {"name": "beta"}}))
        self.assertFalse(match_detection_item(item, {"data": {"name": "gamma"}}))

    def test_contains(self):
        item = detection_item("  sel: {data.field|contains: MIDDLE}\n")
        self.assertTrue(match_detection_item(item, {"data": {"field": "left MIDDLE right"}}))
        self.assertFalse(match_detection_item(item, {"data": {"field": "nope"}}))

    def test_startswith(self):
        item = detection_item("  sel: {data.field|startswith: pre.}\n")
        self.assertTrue(match_detection_item(item, {"data": {"field": "pre.body.tail"}}))
        self.assertFalse(match_detection_item(item, {"data": {"field": "other.body.tail"}}))

    def test_endswith(self):
        item = detection_item("  sel: {data.field|endswith: .ext}\n")
        self.assertTrue(match_detection_item(item, {"data": {"field": "name.ext"}}))
        self.assertFalse(match_detection_item(item, {"data": {"field": "name.other"}}))


# ---- case handling -----------------------------------------------------------------


class TestCaseHandling(unittest.TestCase):
    def test_case_insensitive_by_default_exact(self):
        item = detection_item("  sel: {data.name: AlPha}\n")
        self.assertTrue(match_detection_item(item, {"data": {"name": "alpha"}}))

    def test_case_insensitive_by_default_contains(self):
        item = detection_item("  sel: {data.field|contains: middle}\n")
        self.assertTrue(match_detection_item(item, {"data": {"field": "LEFT MIDDLE RIGHT"}}))

    def test_cased_forces_case_sensitive_exact(self):
        item = detection_item("  sel: {data.name|cased: AlPha}\n")
        self.assertFalse(match_detection_item(item, {"data": {"name": "alpha"}}))
        self.assertTrue(match_detection_item(item, {"data": {"name": "AlPha"}}))

    def test_cased_contains(self):
        item = detection_item("  sel: {data.field|cased|contains: Mid}\n")
        self.assertFalse(match_detection_item(item, {"data": {"field": "a mid value"}}))
        self.assertTrue(match_detection_item(item, {"data": {"field": "a Mid value"}}))

    def test_cased_startswith(self):
        item = detection_item("  sel: {data.field|cased|startswith: Pre}\n")
        self.assertFalse(match_detection_item(item, {"data": {"field": "pre.body"}}))
        self.assertTrue(match_detection_item(item, {"data": {"field": "Pre.body"}}))

    def test_cased_endswith(self):
        item = detection_item("  sel: {data.field|cased|endswith: Ext}\n")
        self.assertFalse(match_detection_item(item, {"data": {"field": "name.ext"}}))
        self.assertTrue(match_detection_item(item, {"data": {"field": "name.Ext"}}))


# ---- missing / list-valued fields --------------------------------------------------


class TestFieldSemantics(unittest.TestCase):
    def test_missing_field_no_match(self):
        # A nested path whose intermediate keys are absent simply does not match.
        item = detection_item("  sel: {data.lvl1.lvl2.key|contains: MIDDLE}\n")
        self.assertFalse(match_detection_item(item, {"data": {"name": "alpha"}}))

    def test_list_valued_field_match_any_element(self):
        item = detection_item("  sel: {data.items|contains: TARGET}\n")
        ev = {"data": {"items": ["first", "has-TARGET-here", "other"]}}
        self.assertTrue(match_detection_item(item, ev))

    def test_list_valued_field_no_element_matches(self):
        item = detection_item("  sel: {data.items|contains: TARGET}\n")
        ev = {"data": {"items": ["first", "other"]}}
        self.assertFalse(match_detection_item(item, ev))

    def test_non_string_scalar_stringified(self):
        item = detection_item("  sel: {data.number: 42}\n")
        self.assertTrue(match_detection_item(item, {"data": {"number": 42}}))
        self.assertFalse(match_detection_item(item, {"data": {"number": 7}}))

    def test_boolean_scalar_stringified(self):
        # A boolean field value is compared as its "True"/"False" string form.
        item = detection_item("  sel: {data.flag: true}\n")
        self.assertTrue(match_detection_item(item, {"data": {"flag": True}}))
        self.assertFalse(match_detection_item(item, {"data": {"flag": False}}))

    def test_structured_field_value_stringified(self):
        # A resolved field that is a list of dicts: each element is stringified, and a
        # contains match looks inside the stringified element (match-any-element).
        item = detection_item("  sel: {data.items|contains: alpha}\n")
        self.assertTrue(match_detection_item(item, {"data": {"items": [{"k": "alpha"}, {"k": "beta"}]}}))
        self.assertFalse(match_detection_item(item, {"data": {"items": [{"k": "gamma"}]}}))

    def test_precomputed_values_text_ignored_for_field_match(self):
        # event_values_text is only consulted for keyword items. For a field match it must
        # be ignored: a stale/unrelated blob must not leak into a field comparison.
        item = detection_item("  sel: {data.name: alpha}\n")
        stale = "completely unrelated blob"
        self.assertTrue(match_detection_item(item, {"data": {"name": "alpha"}}, event_values_text=stale))
        self.assertFalse(match_detection_item(item, {"data": {"name": "beta"}}, event_values_text=stale))


# ---- keywords (whole-event values) -------------------------------------------------


class TestKeywords(unittest.TestCase):
    def test_keyword_hit_inside_brackets_substring_no_tokenization(self):
        # Plain substring, no tokenization: a term matches inside adjacent punctuation.
        item = detection_item("  keywords:\n    - TERM\n", selection="keywords")
        ev = {"message": "value is [TERM] wrapped", "data": {}}
        self.assertTrue(match_detection_item(item, ev))

    def test_keyword_hit_in_nested_data(self):
        item = detection_item("  keywords:\n    - NEEDLE\n", selection="keywords")
        ev = {"message": "x", "data": {"deep": {"nested": "a NEEDLE buried here"}}}
        self.assertTrue(match_detection_item(item, ev))

    def test_keyword_or_over_terms(self):
        item_list = all_items("  keywords:\n    - AAA\n    - BBB\n", selection="keywords")
        # keywords list collapses to a single detection item with multiple values
        self.assertEqual(len(item_list), 1)
        item = item_list[0]
        self.assertTrue(match_detection_item(item, {"message": "has BBB", "data": {}}))
        self.assertFalse(match_detection_item(item, {"message": "has CCC", "data": {}}))

    def test_keyword_values_only_not_field_names(self):
        # A keyword equal to a field NAME must NOT match (we serialize values only).
        item = detection_item("  keywords:\n    - message\n", selection="keywords")
        ev = {"message": "nothing interesting", "data": {"name": "alpha"}}
        self.assertFalse(match_detection_item(item, ev))

    def test_keyword_value_equal_to_field_name_as_value_matches(self):
        # But if "message" appears as an actual VALUE, it matches.
        item = detection_item("  keywords:\n    - message\n", selection="keywords")
        ev = {"message": "the message field", "data": {}}
        self.assertTrue(match_detection_item(item, ev))

    def test_keyword_case_insensitive_by_default(self):
        item = detection_item("  keywords:\n    - term\n", selection="keywords")
        ev = {"message": "saw [TERM]", "data": {}}
        self.assertTrue(match_detection_item(item, ev))

    def test_keyword_precomputed_values_text(self):
        item = detection_item("  keywords:\n    - TERM\n", selection="keywords")
        ev = {"message": "saw [TERM]", "data": {}}
        text = serialize_event_values(ev)
        self.assertTrue(match_detection_item(item, ev, event_values_text=text))

    def test_keyword_matches_numeric_leaf_value(self):
        # Keywords serialize ALL leaf values, including non-strings, so a numeric value
        # buried in data is searchable as its string form.
        item = detection_item("  keywords:\n    - '42'\n", selection="keywords")
        self.assertTrue(match_detection_item(item, {"message": "x", "data": {"number": 42}}))
        self.assertFalse(match_detection_item(item, {"message": "x", "data": {"number": 7}}))

    def test_keyword_matches_boolean_leaf_value(self):
        item = detection_item("  keywords:\n    - 'True'\n", selection="keywords")
        self.assertTrue(match_detection_item(item, {"message": "x", "data": {"flag": True}}))

    def test_plain_keyword_does_not_span_value_separator(self):
        # Two separate leaf values are joined by a newline; a PLAIN (wildcard-free) term
        # must not match across that boundary.
        item = detection_item("  keywords:\n    - foobar\n", selection="keywords")
        ev = {"message": "foo", "data": {"x": "bar"}}  # serialized as "foo\nbar"
        self.assertFalse(match_detection_item(item, ev))

    def test_wildcard_keyword_spans_value_separator(self):
        # Documented edge: because '*' matches any run incl. newlines (re.DOTALL), a WILDCARD
        # term CAN span the value separator. Pins the current, intentional behaviour.
        item = detection_item("  keywords:\n    - 'foo*bar'\n", selection="keywords")
        ev = {"message": "foo", "data": {"x": "bar"}}  # serialized as "foo\nbar"
        self.assertTrue(match_detection_item(item, ev))

    def test_keyword_empty_event_no_match(self):
        item = detection_item("  keywords:\n    - TERM\n", selection="keywords")
        self.assertFalse(match_detection_item(item, {"message": "", "data": {}}))


# ---- value collection helpers ------------------------------------------------------


class TestCollectValues(unittest.TestCase):
    def test_collect_values_recurses_and_excludes_keys(self):
        ev = {"message": "m", "data": {"a": "v1", "b": {"c": "v2"}, "d": [1, "v3"]}}
        vals = collect_values(ev)
        self.assertIn("m", vals)
        self.assertIn("v1", vals)
        self.assertIn("v2", vals)
        self.assertIn("v3", vals)
        self.assertIn("1", vals)
        # keys must not appear
        self.assertNotIn("message", vals)
        self.assertNotIn("data", vals)

    def test_collect_values_handles_none_and_bool(self):
        ev = {"a": None, "b": True, "c": False}
        vals = collect_values(ev)
        self.assertNotIn("None", vals)
        self.assertIn("True", vals)
        self.assertIn("False", vals)


# ---- glob wildcards ----------------------------------------------------------------


class TestWildcards(unittest.TestCase):
    def test_star_interior_exact(self):
        # 'foo*bar' as an exact value = anchored glob: foo, any run, bar.
        item = detection_item("  sel: {data.field: 'foo*bar'}\n")
        self.assertTrue(match_detection_item(item, {"data": {"field": "fooXYZbar"}}))
        self.assertTrue(match_detection_item(item, {"data": {"field": "foobar"}}))  # * matches empty
        self.assertFalse(match_detection_item(item, {"data": {"field": "fooXYZbarZ"}}))  # anchored end
        self.assertFalse(match_detection_item(item, {"data": {"field": "Zfoobar"}}))  # anchored start

    def test_qmark_single_char(self):
        # 'a?b' matches exactly one char between a and b.
        item = detection_item("  sel: {data.field: 'a?b'}\n")
        self.assertTrue(match_detection_item(item, {"data": {"field": "aXb"}}))
        self.assertFalse(match_detection_item(item, {"data": {"field": "ab"}}))  # needs one char
        self.assertFalse(match_detection_item(item, {"data": {"field": "aXYb"}}))  # exactly one

    def test_leading_star(self):
        item = detection_item("  sel: {data.field: '*.ext'}\n")
        self.assertTrue(match_detection_item(item, {"data": {"field": "name.ext"}}))
        self.assertFalse(match_detection_item(item, {"data": {"field": "name.other"}}))

    def test_trailing_star(self):
        item = detection_item("  sel: {data.field: 'pre.body.*'}\n")
        self.assertTrue(match_detection_item(item, {"data": {"field": "pre.body.tail"}}))
        self.assertFalse(match_detection_item(item, {"data": {"field": "other.body.tail"}}))

    def test_star_with_contains_modifier(self):
        # User wildcard combined with the contains modifier (which adds boundary wildcards).
        item = detection_item("  sel: {data.field|contains: 'a*b'}\n")
        self.assertTrue(match_detection_item(item, {"data": {"field": "zz aXYZb zz"}}))
        self.assertTrue(match_detection_item(item, {"data": {"field": "prefix a_b suffix"}}))
        self.assertFalse(match_detection_item(item, {"data": {"field": "no match here"}}))

    def test_wildcard_case_insensitive_by_default(self):
        item = detection_item("  sel: {data.field: 'FOO*BAR'}\n")
        self.assertTrue(match_detection_item(item, {"data": {"field": "fooXbar"}}))

    def test_wildcard_cased(self):
        item = detection_item("  sel: {data.field|cased: 'FOO*BAR'}\n")
        self.assertFalse(match_detection_item(item, {"data": {"field": "fooXbar"}}))
        self.assertTrue(match_detection_item(item, {"data": {"field": "FOOXBAR"}}))

    def test_escaped_star_is_literal(self):
        # '\*' escapes to a literal asterisk (Sigma semantics), not a wildcard.
        item = detection_item("  sel: {data.field: 'a\\*b'}\n")
        self.assertTrue(match_detection_item(item, {"data": {"field": "a*b"}}))
        self.assertFalse(match_detection_item(item, {"data": {"field": "aXYZb"}}))

    def test_escaped_qmark_is_literal(self):
        item = detection_item("  sel: {data.field: 'a\\?b'}\n")
        self.assertTrue(match_detection_item(item, {"data": {"field": "a?b"}}))
        self.assertFalse(match_detection_item(item, {"data": {"field": "aXb"}}))

    def test_regex_metacharacters_in_literal_are_escaped(self):
        # A literal containing regex metacharacters must be matched literally, not as regex.
        item = detection_item("  sel: {data.field: 'a.b*'}\n")
        self.assertTrue(match_detection_item(item, {"data": {"field": "a.bXYZ"}}))
        self.assertFalse(match_detection_item(item, {"data": {"field": "aXbYZ"}}))  # '.' is literal

    def test_wildcard_in_keyword(self):
        # Wildcards also work on the whole-event keyword surface.
        item = detection_item("  keywords:\n    - 'alpha*gamma'\n", selection="keywords")
        ev = {"message": "sees alpha-beta-gamma here", "data": {}}
        self.assertTrue(match_detection_item(item, ev))
        ev2 = {"message": "sees alpha-beta here", "data": {}}
        self.assertFalse(match_detection_item(item, ev2))

    def test_wildcard_list_valued_field(self):
        item = detection_item("  sel: {data.items: 'al*a'}\n")
        self.assertTrue(match_detection_item(item, {"data": {"items": ["beta", "alpha"]}}))
        self.assertFalse(match_detection_item(item, {"data": {"items": ["beta", "gamma"]}}))


if __name__ == "__main__":
    unittest.main()
