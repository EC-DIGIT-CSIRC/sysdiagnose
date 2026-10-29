"""
sigmascan rule loader.

Discovers Sigma-shaped YAML rules from a directory tree, parses and validates each with
pySigma, enforces the supported operator/modifier allow-list, and extracts the custom
``logsource.modules`` scoping list.

Fail-soft per rule: a broken, unsupported, or unknown-module rule is logged via
``logger.error`` (naming the file and reason) and skipped; the remaining rules still load
and the run continues.

pySigma owns schema validation (required fields, UUID ``id``, mandatory ``logsource``,
``condition`` grammar, modifier parsing). This module owns what pySigma does not: the
modifier allow-list and the ``logsource.modules`` extraction/validation.
"""

import glob
import os
from collections.abc import Iterator
from dataclasses import dataclass

import yaml
from sigma.exceptions import SigmaError
from sigma.modifiers import (
    SigmaCaseSensitiveModifier,
    SigmaContainsModifier,
    SigmaEndswithModifier,
    SigmaStartswithModifier,
)
from sigma.rule import SigmaDetection, SigmaDetectionItem, SigmaRule

from sysdiagnose.utils.logger import logger

# Default in-SAF rules directory, overridable via SYSDIAGNOSE_SIGMA_RULES_PATH.
# Mirrors yarascan's ./yara / SYSDIAGNOSE_YARA_RULES_PATH convention.
DEFAULT_RULES_PATH = "./sigma"
RULES_PATH_ENV_VAR = "SYSDIAGNOSE_SIGMA_RULES_PATH"

# Supported operator/modifier allow-list. pySigma parses far more than this; our allow-list
# rejects everything else (regex, base64, cidr, numeric, aggregation, ...).
# Note: the `|cased` keyword maps to pySigma's SigmaCaseSensitiveModifier.
ALLOWED_MODIFIERS: frozenset = frozenset(
    {
        SigmaContainsModifier,
        SigmaStartswithModifier,
        SigmaEndswithModifier,
        SigmaCaseSensitiveModifier,
    }
)


class RuleValidationError(Exception):
    """Raised when a rule is valid Sigma but violates a sigmascan v1 constraint
    (e.g. an unsupported operator/modifier, or an unknown target module)."""


@dataclass
class LoadedRule:
    """A validated sigmascan rule ready for evaluation.

    Attributes:
        rule: the parsed pySigma ``SigmaRule``.
        modules: the target modules from ``logsource.modules``, or ``None`` for an
            all-modules rule (``logsource`` with no ``modules`` key).
        source_path: the file the rule was loaded from (for diagnostics).
    """

    rule: SigmaRule
    modules: tuple[str, ...] | None
    source_path: str

    @property
    def id(self) -> str:
        """The rule's UUID as a string, or an empty string if absent."""
        return str(self.rule.id) if self.rule.id is not None else ""

    @property
    def title(self) -> str:
        """The rule's human-readable title, or an empty string if absent."""
        return self.rule.title or ""

    @property
    def is_all_modules(self) -> bool:
        """True if the rule targets every module (no ``logsource.modules`` key)."""
        return self.modules is None


def get_rules_path() -> str:
    """Return the configured rules directory (env override or default)."""
    return os.getenv(RULES_PATH_ENV_VAR, DEFAULT_RULES_PATH)


def discover_rule_files(rules_path: str) -> list[str]:
    """Recursively discover ``*.yml`` and ``*.yaml`` files under ``rules_path``."""
    files: list[str] = []
    for ext in ("*.yml", "*.yaml"):
        files.extend(glob.glob(os.path.join(rules_path, "**", ext), recursive=True))
    # Deterministic order for stable logging / testing.
    return sorted({f for f in files if os.path.isfile(f)})


def extract_modules(rule: SigmaRule) -> tuple[str, ...] | None:
    """Read the custom ``logsource.modules`` list from a parsed rule.

    Returns a tuple of module names (de-duplicated, first-seen order preserved), or ``None``
    for an all-modules rule.

    pySigma parses ``product``/``category``/``service`` natively and preserves any other
    key under ``logsource`` in ``custom_attributes``. For an all-modules rule
    (``logsource: {product: ios}``), ``custom_attributes`` is ``None``.

    Raises:
        RuleValidationError: if ``modules`` is present but not a list of non-empty strings.
    """
    attrs = rule.logsource.custom_attributes
    if not attrs or "modules" not in attrs:
        return None

    modules = attrs["modules"]
    if not isinstance(modules, list) or not modules:
        raise RuleValidationError("logsource.modules must be a non-empty list of module names")
    for m in modules:
        if not isinstance(m, str) or not m.strip():
            raise RuleValidationError(f"logsource.modules entries must be non-empty strings, got {m!r}")
    # De-duplicate while preserving first-seen order (a duplicate module name is harmless
    # but would otherwise scan the same source twice for this rule).
    return tuple(dict.fromkeys(modules))


def iter_detection_items(detection: SigmaDetection) -> Iterator[SigmaDetectionItem]:
    """Yield every leaf ``SigmaDetectionItem`` in a detection, recursing into nested
    ``SigmaDetection`` objects.

    A selection written as a **list of maps** (``sel: [- {...}, - {...}]``) nests
    ``SigmaDetection`` objects inside ``detection_items`` rather than exposing flat
    ``SigmaDetectionItem``s. Any code that inspects ``.field``/``.value``/``.modifiers`` must
    recurse, or it both misses nested items and crashes on the nested ``SigmaDetection``
    (which has no such attributes).
    """
    for element in detection.detection_items:
        if isinstance(element, SigmaDetectionItem):
            yield element
        elif isinstance(element, SigmaDetection):
            yield from iter_detection_items(element)


def _check_modifier_allow_list(rule: SigmaRule) -> None:
    """Reject a rule that uses any modifier outside the supported allow-list.

    Recurses into nested (list-of-maps) detections so a modifier buried there is still
    checked rather than bypassing the allow-list.

    Raises:
        RuleValidationError: naming the first unsupported modifier found.
    """
    for selection_name, detection in rule.detection.detections.items():
        for item in iter_detection_items(detection):
            for modifier in getattr(item, "modifiers", []) or []:
                if modifier not in ALLOWED_MODIFIERS:
                    raise RuleValidationError(
                        f"unsupported modifier {modifier.__name__} in selection '{selection_name}'"
                        f" (field {getattr(item, 'field', None)!r}); supported:"
                        f" contains/startswith/endswith/cased"
                    )


def _validate_condition_parses(rule: SigmaRule) -> None:
    """Force-parse every condition so a broken condition is caught at load, not mid-scan.

    pySigma parses the ``condition`` string lazily, so ``from_yaml`` succeeds even when the
    condition references an undefined selection or uses unsupported syntax. Parsing here
    surfaces that error at load time so the rule is logged and skipped like any other.
    """
    for parsed in rule.detection.parsed_condition:
        parsed.parse()


def _validate_modules_known(
    modules: tuple[str, ...] | None, known_modules: set[str] | None, source_path: str
) -> tuple[str, ...] | None:
    """Validate target modules against the known parser/analyser set.

    ``known_modules`` is the set of module names SAF can produce, supplied by the caller.
    When ``None``, the check is deferred (no discovery context) and ``modules`` is returned
    unchanged.

    Unknown module names are dropped and reported via ``logger.error``, while the rule is
    kept for its known modules — so a typo in one entry does not lose the valid entries.
    Only when every listed module is unknown is the rule rejected.

    Args:
        modules: the rule's target modules, or ``None`` for an all-modules rule.
        known_modules: the set of known module names, or ``None`` to defer the check.
        source_path: the rule's file, for the log message.

    Returns:
        The known target modules to keep, or ``None`` for an all-modules rule (or when the
        check is deferred).

    Raises:
        RuleValidationError: only if all listed modules are unknown.
    """
    if modules is None or known_modules is None:
        return modules

    known = tuple(m for m in modules if m in known_modules)
    unknown = [m for m in modules if m not in known_modules]

    if not unknown:
        return modules

    if not known:
        # every module unknown -> nothing to scan, reject the whole rule
        raise RuleValidationError(f"unknown module(s) in logsource.modules: {unknown}")

    # Some known, some unknown -> keep the known ones, report the unknown ones loudly.
    # The message names ONLY the dropped (unknown) modules; it deliberately does not list
    # the kept module names, so the error is unambiguously about what failed.
    logger.error(
        f"sigmascan rule {source_path}: dropping unknown module(s) {unknown} from"
        f" logsource.modules; rule still applies to its other known module(s)",
        extra={"sigma_rule_file": source_path},
    )
    return known


def load_rule_from_yaml(text: str, source_path: str, known_modules: set[str] | None = None) -> LoadedRule:
    """Parse and validate a single rule from YAML text.

    When ``known_modules`` is supplied, unknown entries in ``logsource.modules`` are dropped
    (and logged) while the rule is kept for its known modules; the returned rule's
    ``modules`` reflects only the kept ones. The rule is rejected only if **all** its
    modules are unknown (see ``_validate_modules_known``).

    Raises:
        SigmaError: for any Sigma schema/grammar error (bad UUID, missing detection/
            logsource, bad condition, ...) — raised by pySigma.
        RuleValidationError: for a sigmascan v1 constraint violation (unsupported modifier,
            malformed ``logsource.modules``, or **all** target modules unknown).
    """
    rule = SigmaRule.from_yaml(text)
    _check_modifier_allow_list(rule)
    _validate_condition_parses(rule)
    modules = extract_modules(rule)
    modules = _validate_modules_known(modules, known_modules, source_path)
    return LoadedRule(rule=rule, modules=modules, source_path=source_path)


def load_rules(rules_path: str | None = None, known_modules: set[str] | None = None) -> list[LoadedRule]:
    """Load all valid rules from the rules directory tree (fail-soft per rule).

    Args:
        rules_path: rules directory; defaults to the env override or ``./sigma``.
        known_modules: set of known module names for ``logsource.modules`` validation.
            When ``None``, the unknown-module check is deferred.

    Returns:
        A ``LoadedRule`` list for every file that parsed and validated. Invalid rules (schema
        errors, unsupported modifiers, malformed YAML, unreadable files, all-unknown modules)
        are logged at error level and skipped. A missing rules directory or no valid rules at
        all is a warning (a configuration state, not a failure); a duplicate ``id`` is a
        warning.
    """
    if rules_path is None:
        rules_path = get_rules_path()

    if not os.path.isdir(rules_path):
        logger.warning(f"sigmascan rules directory not found: {rules_path}")
        return []

    loaded: list[LoadedRule] = []
    for rule_file in discover_rule_files(rules_path):
        try:
            with open(rule_file) as f:
                text = f.read()
            loaded.append(load_rule_from_yaml(text, rule_file, known_modules=known_modules))
            logger.info(f"Loaded sigmascan rule: {rule_file}", extra={"sigma_rule_file": rule_file})
        except (SigmaError, RuleValidationError, yaml.YAMLError) as e:
            # yaml.YAMLError catches a syntactically broken file (pySigma reads YAML before
            # validating), so it is skipped like any other bad rule rather than crashing.
            logger.error(
                f"Skipping invalid sigmascan rule {rule_file}: {e}",
                extra={"sigma_rule_file": rule_file},
            )
        except OSError as e:
            logger.error(
                f"Skipping unreadable sigmascan rule {rule_file}: {e}",
                extra={"sigma_rule_file": rule_file},
            )

    _warn_duplicate_ids(loaded)

    if not loaded:
        # No rules is a configuration state, not an execution failure — warn (don't error)
        # so an otherwise-clean run isn't marked ERROR in its summary.
        logger.warning(f"No valid sigmascan rules loaded from {rules_path}")
    else:
        logger.info(f"Loaded {len(loaded)} sigmascan rule(s) from {rules_path}")
    return loaded


def _warn_duplicate_ids(loaded: list[LoadedRule]) -> None:
    """Warn about rules sharing the same UUID ``id`` across files.

    Harmless (ids aren't used as keys) but usually a copy-paste mistake, so it's reported as
    a warning naming the id and the files.
    """
    by_id: dict[str, list[str]] = {}
    for lr in loaded:
        if lr.id:
            by_id.setdefault(lr.id, []).append(lr.source_path)
    for rule_id, paths in by_id.items():
        if len(paths) > 1:
            logger.warning(
                f"duplicate sigmascan rule id {rule_id} shared by {len(paths)} rules: {paths}",
                extra={"sigma_rule_id": rule_id},
            )
