"""
sigmascan — SAF detection-rule engine analyser.

Loads Sigma-shaped YAML detection rules and evaluates them against a case's parsed event
stream, emitting one alert per match (``module=sigmascan``, full matched event embedded).
A structured successor to ``yarascan``.

Execution: build an inverted ``module -> rules`` index, then scan each present module once,
loading its source once and evaluating every targeting rule per event. Rules are compiled
once and reused across events.

Rules are discovered from the rules directory (default ``./sigma`` or
``SYSDIAGNOSE_SIGMA_RULES_PATH``), mirroring ``yarascan``.
"""

from collections import defaultdict
from collections.abc import Iterable

from sysdiagnose.sigmascan.condition import CompiledRule
from sysdiagnose.sigmascan.emit import build_alert
from sysdiagnose.sigmascan.loader import LoadedRule, load_rules
from sysdiagnose.sigmascan.logsource import build_module_index, discover_modules
from sysdiagnose.sigmascan.matcher import serialize_event_values
from sysdiagnose.utils.base import BaseAnalyserInterface, SysdiagnoseConfig, logger

# The five Sigma severity levels, always present in a summary.
SIGMA_LEVELS = ("critical", "high", "medium", "low", "informational")


class SigmascanAnalyser(BaseAnalyserInterface):
    """Scan parsed data with Sigma-shaped detection rules."""

    description = "Scan parsed data with Sigma-shaped detection rules ('./sigma' or SYSDIAGNOSE_SIGMA_RULES_PATH)"
    format = "jsonl"
    # A scanner: its output is findings, not a data source — not scanned by itself or others.
    scannable = False

    def __init__(self, config: SysdiagnoseConfig, case: dict) -> None:
        """Initialise the analyser for a case (module name derived from this file)."""
        super().__init__(__file__, config, case)

    def execute(self) -> list:
        """Load rules, build the module index, and scan each present module once.

        Returns one alert dict per match (full event embedded); zero matches yields an empty
        list (an empty ``sigmascan.jsonl`` — success, not an error).
        """
        modules = discover_modules(self.config)
        rules = load_rules(known_modules=modules)
        if not rules:
            # load_rules already logged why (missing dir / no valid rules).
            return []

        index = build_module_index(rules, modules)
        if not index:
            logger.info("sigmascan: no rules target any discovered module")
            return []

        # Compile each rule once and reuse everywhere it is scanned — an all-modules rule
        # targets many modules, so compiling per module would recompile it repeatedly.
        compiled_by_rule = {id(lr): CompiledRule(lr.rule) for lr in rules}

        alerts: list[dict] = []
        for module, module_rules in index.items():
            pairs = [(lr, compiled_by_rule[id(lr)]) for lr in module_rules]
            alerts.extend(self.scan_module(module, pairs))
        return alerts

    def scan_module(self, module: str, rules: list[tuple[LoadedRule, CompiledRule]]) -> list[dict]:
        """Scan one module's events against the rules targeting it.

        Loads the module's output once, streams its events, and returns one alert per match.
        A module with no output for this case is a quiet no-op. Rules arrive pre-compiled;
        the per-event keyword blob is built once per event.

        Kept stateless and streaming (alerts collected by plain append) so it can later be
        mapped over a worker pool.

        Args:
            module: the module name being scanned.
            rules: ``(LoadedRule, CompiledRule)`` pairs targeting this module.
        """
        events = self._load_module_events(module)
        if events is None:
            return []  # no output for this case — quiet no-op

        alerts: list[dict] = []
        for event in events:
            if not isinstance(event, dict):
                continue  # non-dict entries are not matchable events
            values_text = serialize_event_values(event)
            for loaded_rule, compiled_rule in rules:
                if compiled_rule.evaluate(event, event_values_text=values_text):
                    alerts.append(build_alert(loaded_rule, event, module))
        return alerts

    def _load_module_events(self, module: str):
        """Load a module's output as an iterable of event dicts, or ``None`` if no output.

        Handles the result shapes ``get_result()`` can return: a ``list`` or a streaming
        ``generator`` of events (e.g. logarchive) are iterated lazily; a bare ``dict`` (a
        json module) is wrapped as one event; ``str``/``bytes`` are not events and skipped.
        A source that fails to load is logged and treated as no output, so one bad source
        never aborts the scan.
        """
        cls = self.config.get_module_class(module)
        if cls is None:
            # Shouldn't happen — the index is built from discovered modules.
            logger.error(f"sigmascan: module {module!r} resolved to no producing class")
            return None

        try:
            instance = cls(self.config, self.case)
            if not instance.output_exists():
                return None
            result = instance.get_result()
        except Exception as ex:
            logger.exception(f"sigmascan: failed to load module {module!r}: {ex}")
            return None

        if result is None:
            return None
        if isinstance(result, dict):
            return [result]  # single json object -> one event
        if isinstance(result, (str, bytes)):
            # Defensive: text formats are already filtered out of the scannable set.
            logger.debug(f"sigmascan: module {module!r} result is text, not events; skipping")
            return None
        if isinstance(result, Iterable):
            return result  # list/generator of events, iterated lazily
        logger.warning(f"sigmascan: module {module!r} result is not iterable; skipping")
        return None


def build_summary(alerts: list[dict]) -> dict:
    """Roll up alerts by Sigma ``level`` for quick triage.

    Pure function of the alerts. All five Sigma levels are always present; per level: total
    ``count`` plus a per-rule breakdown ``[{id, title, count}]`` sorted by count descending.
    An alert with a missing/unknown level is bucketed under ``informational``.
    """
    # level -> {(id, title) -> count}
    per_level: dict[str, dict[tuple[str, str], int]] = {lvl: defaultdict(int) for lvl in SIGMA_LEVELS}

    for alert in alerts:
        data = alert.get("data", {}) if isinstance(alert, dict) else {}
        level = data.get("level") or "informational"
        if level not in per_level:
            level = "informational"
        key = (data.get("rule_id", ""), data.get("rule_title", ""))
        per_level[level][key] += 1

    summary: dict = {}
    for level in SIGMA_LEVELS:
        rule_counts = per_level[level]
        rules_list = [{"id": rid, "title": title, "count": count} for (rid, title), count in rule_counts.items()]
        rules_list.sort(key=lambda r: r["count"], reverse=True)
        summary[level] = {
            "count": sum(r["count"] for r in rules_list),
            "rules": rules_list,
        }
    return summary
