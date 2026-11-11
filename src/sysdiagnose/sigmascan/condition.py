"""
sigmascan condition evaluator.

Walks pySigma's already-parsed condition tree and calls the leaf matcher at each leaf.
pySigma owns the ``condition`` grammar — ``and``/``or``/``not``, parentheses, and the
``1 of``/``all of`` quantifiers (expanded into ``ConditionOR``/``ConditionAND`` trees); this
module only evaluates the result against a SAF event.

Handled node types (from ``sigma.conditions``; anything else raises``ConditionEvaluationError``): 
* ``ConditionAND``/``ConditionOR`` (boolean over ``.args``)
* ``ConditionNOT`` (unary, ``.args[0]``)
*  ``ConditionFieldEqualsValueExpression`` (field leaf → ``match_field_value``)
* ``ConditionValueExpression`` (keyword leaf → ``match_keyword_value``).

Recovering modifiers: a condition leaf exposes ``.field``/``.value`` but carries NO modifiers
at all. Operator modifiers (``contains``/``startswith``/``endswith``) survive indirectly in
the leaf's ``value``/``operator``, but ``cased`` is a pure matching policy with no such trace
— drop it and every rule silently matches case-insensitively. So we map each leaf back to its
owning ``SigmaDetectionItem`` (which keeps ``.modifiers``) via value-object identity:
``id(leaf.value)`` (see ``_build_value_index``). This relies on a pySigma implementation
detail — it reuses the same value object in leaf and item — asserted in cased-through-condition tests).

Compilation: ``SigmaCondition.parse()`` deep-copies the tree and re-runs postprocessing on
every call (too expensive per event), so :class:`CompiledRule` builds the parsed tree(s) and
value index once per rule and reuses them read-only across events.
"""

from sigma.conditions import (
    ConditionAND,
    ConditionFieldEqualsValueExpression,
    ConditionNOT,
    ConditionOR,
    ConditionValueExpression,
)
from sigma.rule import SigmaDetectionItem, SigmaRule

from sysdiagnose.sigmascan.loader import iter_detection_items
from sysdiagnose.sigmascan.matcher import (
    match_field_value,
    match_keyword_value,
    serialize_event_values,
)


class ConditionEvaluationError(Exception):
    """Raised when the condition tree contains a node type we do not support."""


def _build_value_index(rule: SigmaRule) -> dict[int, SigmaDetectionItem]:
    """Index every detection item by the ``id()`` of each value object it holds.

    Lets a condition leaf recover its detection item (and thus its modifiers, including
    ``cased``) by ``id(leaf.value)``.
    """
    index: dict[int, SigmaDetectionItem] = {}
    for detection in rule.detection.detections.values():
        for item in iter_detection_items(detection):
            for value in item.value:
                index[id(value)] = item
    return index


def _modifiers_for_leaf(leaf: object, value_index: dict[int, SigmaDetectionItem]) -> list:
    """Return the modifiers of the detection item owning this leaf's value.

    Empty list if the value is not indexed (shouldn't happen for a valid rule; keeps
    evaluation robust rather than crashing).
    """
    item = value_index.get(id(leaf.value))
    if item is None:
        return []
    return list(getattr(item, "modifiers", []) or [])


def _evaluate_node(
    node: object,
    event: dict,
    value_index: dict[int, SigmaDetectionItem],
    event_values_text: str,
) -> bool:
    """Recursively evaluate one condition-tree node against the event."""
    if isinstance(node, ConditionAND):
        return all(_evaluate_node(arg, event, value_index, event_values_text) for arg in node.args)
    if isinstance(node, ConditionOR):
        return any(_evaluate_node(arg, event, value_index, event_values_text) for arg in node.args)
    if isinstance(node, ConditionNOT):
        return not _evaluate_node(node.args[0], event, value_index, event_values_text)
    if isinstance(node, ConditionValueExpression):
        # keyword leaf: whole-event value match
        modifiers = _modifiers_for_leaf(node, value_index)
        return match_keyword_value(node.value, modifiers, event, event_values_text)
    if isinstance(node, ConditionFieldEqualsValueExpression):
        # field leaf: dotted-path match
        modifiers = _modifiers_for_leaf(node, value_index)
        return match_field_value(node.field, node.value, modifiers, event)
    raise ConditionEvaluationError(f"unsupported condition node type: {type(node).__name__}")


class CompiledRule:
    """A rule compiled once for repeated evaluation across many events.

    pySigma's ``SigmaCondition.parse()`` deepcopies the condition tree on every call, so
    parsing it inside the per-event loop is expensive. The parsed tree(s) and the
    value→detection-item index depend only on the rule, so they are built once here and
    reused (read-only) for every event.
    """

    def __init__(self, rule: SigmaRule) -> None:
        """Parse and cache the rule's condition tree(s) and value index."""
        self.rule = rule
        self._value_index = _build_value_index(rule)
        # one parsed tree per condition string; a list-valued `condition:` is OR-combined
        self._condition_trees = [parsed.parse() for parsed in rule.detection.parsed_condition]

    def evaluate(self, event: dict, event_values_text: str | None = None) -> bool:
        """Return True if the compiled rule matches ``event``.

        Args:
            event: the SAF event dict (top-level + nested ``data.*``).
            event_values_text: optional pre-serialized event values for keyword leaves; built
                on demand if not supplied. A caller scanning many events should build it once
                per event with ``serialize_event_values(event)`` and pass it in.
        """
        if event_values_text is None:
            event_values_text = serialize_event_values(event)
        return any(_evaluate_node(tree, event, self._value_index, event_values_text) for tree in self._condition_trees)


def evaluate_rule(rule: SigmaRule, event: dict, event_values_text: str | None = None) -> bool:
    """Return True if ``rule`` matches ``event``.

    Convenience wrapper that compiles and evaluates one event. To scan many events against
    the same rule, build a :class:`CompiledRule` once and call ``.evaluate()`` per event,
    which avoids re-parsing the condition tree each time.

    Raises:
        ConditionEvaluationError: for an unsupported condition node type.
        UnsupportedMatchError: for an unsupported special character in a leaf value.
    """
    return CompiledRule(rule).evaluate(event, event_values_text)
