"""
sigmascan leaf matcher.

This is the only part of the engine that pySigma cannot provide: deciding whether a single
parsed Sigma detection item (``SigmaDetectionItem``) matches *our* nested SAF event dict.

pySigma gives us, per detection item:
- ``item.field``   : the field name as an opaque dotted string, or ``None`` for keywords.
- ``item.modifiers``: a list of modifier *classes* (``SigmaContainsModifier`` etc.).
- ``item.value``   : a list of values (``SigmaString``/``SigmaNumber``/``SigmaBool``);
                     a plain value list is OR-linked ("equals any of").

The matcher resolves the dotted field path into the nested event, derives the operator from
the modifier set, and compares — honouring Sigma semantics:

- Missing field → no match (never an error).
- List-valued resolved field → match if ANY element matches.
- Value list on the item → match if ANY value matches ("equals any of").
- Case-insensitive by default; the ``cased`` modifier forces case-sensitive.
- Glob wildcards ``*`` (any run) and ``?`` (single char) are supported in field values and
  keywords. A literal ``*``/``?`` is written escaped (``\\*``/``\\?``). A wildcard-free value
  uses a fast plain string comparison; a wildcard value compiles to an anchored regex
  (cached).
- Keywords (``field is None``) match over the event's serialized leaf *values* only (never
  keys/punctuation), serialized once per event.

The matcher is a pure function of (detection item, event).
"""

import re
from functools import lru_cache

from sigma.modifiers import (
    SigmaCaseSensitiveModifier,
    SigmaContainsModifier,
    SigmaEndswithModifier,
    SigmaStartswithModifier,
)
from sigma.rule import SigmaDetectionItem
from sigma.types import SigmaString, SpecialChars

# ---- operator tags -----------------------------------------------------------------

OP_EXACT = "exact"
OP_CONTAINS = "contains"
OP_STARTSWITH = "startswith"
OP_ENDSWITH = "endswith"

_MODIFIER_TO_OP = {
    SigmaContainsModifier: OP_CONTAINS,
    SigmaStartswithModifier: OP_STARTSWITH,
    SigmaEndswithModifier: OP_ENDSWITH,
}

# Internal pattern token markers (private, stable sentinels used only inside this module).
_STAR = "\x00*"  # matches any run of characters (Sigma '*')
_QMARK = "\x00?"  # matches exactly one character (Sigma '?')


class UnsupportedMatchError(Exception):
    """Raised when a detection item cannot be evaluated by the v1 matcher."""


# ---- field resolution --------------------------------------------------------------

_MISSING = object()


def resolve_field(event: dict, dotted_path: str) -> object:
    """Resolve a dotted path into the nested event dict.

    Splits on ``.`` and walks the dict. Returns the resolved value, or the sentinel
    ``_MISSING`` if any intermediate key is absent or not a dict.
    """
    current = event
    for key in dotted_path.split("."):
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return _MISSING
    return current


# ---- pattern extraction from Sigma values ------------------------------------------


def _pattern_tokens(value: object) -> list[str]:
    """Turn a Sigma value into a flat token list of literal strings and wildcard markers.

    ``SigmaString.s`` is a tuple of literal fragments interleaved with ``SpecialChars``
    markers (``WILDCARD_MULTI`` for ``*``, ``WILDCARD_SINGLE`` for ``?``). Escaped literals
    (``\\*``, ``\\?``) are already collapsed by pySigma into plain string fragments, so they
    arrive here as ordinary literal text — exactly the "match a literal asterisk" behaviour.

    Non-string values (numbers, booleans) become a single literal token.
    """
    if not isinstance(value, SigmaString):
        return [str(value)]

    tokens: list[str] = []
    for fragment in value.s:
        if isinstance(fragment, str):
            tokens.append(fragment)
        elif fragment == SpecialChars.WILDCARD_MULTI:
            tokens.append(_STAR)
        elif fragment == SpecialChars.WILDCARD_SINGLE:
            tokens.append(_QMARK)
        else:
            raise UnsupportedMatchError(f"unsupported special character in value {str(value)!r}")
    return tokens


def _has_wildcard(tokens: list[str]) -> bool:
    """True if the token list contains a glob wildcard marker (``*`` or ``?``)."""
    return any(t is _STAR or t is _QMARK for t in tokens)


def _literal_of(tokens: list[str]) -> str:
    """Join a wildcard-free token list into its literal string."""
    return "".join(tokens)


# ---- regex compilation (wildcard path) ---------------------------------------------


@lru_cache(maxsize=4096)
def _compile_pattern(regex_body: str, anchor_start: bool, anchor_end: bool, cased: bool) -> re.Pattern:
    """Compile and cache an anchored regex for a wildcard pattern.

    ``regex_body`` is the already-translated body (literals escaped, ``*``→``.*``,
    ``?``→``.``). Anchoring is applied here so the same body can be reused across operators.
    """
    pattern = regex_body
    if anchor_start:
        pattern = "^" + pattern
    if anchor_end:
        pattern = pattern + "$"
    flags = 0 if cased else re.IGNORECASE
    return re.compile(pattern, flags | re.DOTALL)


def _regex_body(tokens: list[str]) -> str:
    """Translate a token list into a regex body: literals escaped, ``*``→``.*``, ``?``→``.``."""
    out: list[str] = []
    for t in tokens:
        if t is _STAR:
            out.append(".*")
        elif t is _QMARK:
            out.append(".")
        else:
            out.append(re.escape(t))
    return "".join(out)


def _wildcard_match(haystack: str, tokens: list[str], operator: str, cased: bool) -> bool:
    """Match a wildcard pattern against one string, with operator-driven anchoring."""
    body = _regex_body(tokens)
    if operator == OP_EXACT:
        anchor_start, anchor_end = True, True
    elif operator == OP_STARTSWITH:
        anchor_start, anchor_end = True, False
    elif operator == OP_ENDSWITH:
        anchor_start, anchor_end = False, True
    else:  # OP_CONTAINS
        anchor_start, anchor_end = False, False
    pattern = _compile_pattern(body, anchor_start, anchor_end, cased)
    # search() works for all anchoring combinations because anchors are baked into the body.
    return pattern.search(haystack) is not None


# ---- operator / modifier helpers ---------------------------------------------------


def _operator_for(modifiers: list) -> str:
    """Derive the match operator from the detection item's modifier classes."""
    for mod in modifiers:
        if mod in _MODIFIER_TO_OP:
            return _MODIFIER_TO_OP[mod]
    return OP_EXACT


def _is_cased(modifiers: list) -> bool:
    """True if the ``cased`` modifier is present (force case-sensitive matching)."""
    return SigmaCaseSensitiveModifier in modifiers


# ---- leaf value comparison ---------------------------------------------------------


def _compare_tokens(haystack: str, tokens: list[str], operator: str, cased: bool) -> bool:
    """Compare one resolved string against one value's token list.

    Fast path: a wildcard-free value uses plain string ops (no regex). Wildcard values go
    through the compiled, cached regex path.
    """
    if _has_wildcard(tokens):
        return _wildcard_match(haystack, tokens, operator, cased)

    needle = _literal_of(tokens)
    if not cased:
        haystack = haystack.lower()
        needle = needle.lower()

    if operator == OP_EXACT:
        return haystack == needle
    if operator == OP_CONTAINS:
        return needle in haystack
    if operator == OP_STARTSWITH:
        return haystack.startswith(needle)
    if operator == OP_ENDSWITH:
        return haystack.endswith(needle)
    return False  # unreachable with the derived operator set


def _stringify_resolved(value: object) -> list[str]:
    """Flatten a resolved field value into the list of string candidates to compare.

    A list-valued field yields one candidate per element (match-any-element, Sigma). A
    scalar yields a single candidate. ``None`` yields an empty list (no candidate matches).
    Non-string scalars are stringified so e.g. ``data.pid: 42`` can match the term ``42``.
    """
    if value is _MISSING or value is None:
        return []
    if isinstance(value, list):
        out: list[str] = []
        for element in value:
            if element is None:
                continue
            out.append(element if isinstance(element, str) else str(element))
        return out
    return [value if isinstance(value, str) else str(value)]


# ---- whole-event keyword surface ---------------------------------------------------


def collect_values(event: object) -> list[str]:
    """Recursively collect all leaf *values* of the event as strings.

    Field names and punctuation are excluded, so a keyword like ``message`` cannot match
    every event by hitting a field name.
    """
    out: list[str] = []

    def _walk(node: object) -> None:
        """Recurse into containers, appending each scalar leaf value to ``out``."""
        if isinstance(node, dict):
            for v in node.values():
                _walk(v)
        elif isinstance(node, (list, tuple)):
            for v in node:
                _walk(v)
        elif node is None:
            return
        elif isinstance(node, bool):
            out.append(str(node))
        elif isinstance(node, str):
            out.append(node)
        else:
            out.append(str(node))

    _walk(event)
    return out


def serialize_event_values(event: object) -> str:
    """Join all leaf values into a single text blob for keyword search.

    Built once per event by the caller and reused across keyword terms. The newline
    separator keeps adjacent values from forming accidental cross-value matches, though a
    wildcard term can still span it (``re.DOTALL``) — an accepted edge for keywords.
    """
    return "\n".join(collect_values(event))


def match_keyword_tokens(tokens: list[str], event_values_text: str, cased: bool) -> bool:
    """Match one keyword term (as tokens) over the pre-serialized event values.

    Keywords use ``contains`` semantics (the term may appear anywhere in the event values).
    """
    return _compare_tokens(event_values_text, tokens, OP_CONTAINS, cased)


# ---- single-value entry points -----------------------------------------------------


def match_keyword_value(value: object, modifiers: list, event: dict, event_values_text: str | None = None) -> bool:
    """Return True if one keyword value matches the whole-event values surface.

    Used both by ``match_detection_item`` (OR over a keyword list) and by the condition
    walker, where pySigma has already expanded a keyword list into one leaf per value.
    """
    cased = _is_cased(modifiers)
    if event_values_text is None:
        event_values_text = serialize_event_values(event)
    tokens = _pattern_tokens(value)
    return match_keyword_tokens(tokens, event_values_text, cased)


def match_field_value(field: str, value: object, modifiers: list, event: dict) -> bool:
    """Return True if one field value matches the event at ``field`` (dotted path).

    Resolves the dotted path, then applies the operator (derived from ``modifiers``) against
    every candidate of a possibly list-valued resolved field (match-any-element). Missing
    field -> no match.
    """
    cased = _is_cased(modifiers)
    operator = _operator_for(modifiers)
    candidates = _stringify_resolved(resolve_field(event, field))
    if not candidates:
        return False
    tokens = _pattern_tokens(value)
    return any(_compare_tokens(candidate, tokens, operator, cased) for candidate in candidates)


# ---- public entry point ------------------------------------------------------------


def match_detection_item(item: SigmaDetectionItem, event: dict, event_values_text: str | None = None) -> bool:
    """Return True if a single parsed ``SigmaDetectionItem`` matches the event.

    OR over the item's value list ("equals any of" / keyword OR). Delegates to the
    single-value entry points so the same comparison logic backs both this and the
    condition walker.

    Args:
        item: a pySigma ``SigmaDetectionItem`` (``field``/``modifiers``/``value``).
        event: the SAF event dict (top-level + nested ``data.*``).
        event_values_text: optional pre-serialized event values for keyword items; built
            on demand if not supplied. Callers scanning many items against one event should
            build it once with ``serialize_event_values(event)`` and pass it in.

    Raises:
        UnsupportedMatchError: if a value carries an unsupported special character.
    """
    modifiers = list(getattr(item, "modifiers", []) or [])
    values = list(item.value)

    # Keywords: field is None -> whole-event value match (OR over terms, contains semantics).
    if getattr(item, "field", None) is None:
        if event_values_text is None:
            event_values_text = serialize_event_values(event)
        return any(match_keyword_value(v, modifiers, event, event_values_text) for v in values)

    return any(match_field_value(item.field, v, modifiers, event) for v in values)
