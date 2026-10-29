"""
sigmascan alert construction.

Builds one alert per rule match in the SAF event shape: ``module=sigmascan``, the full
matched event embedded under ``data.event``, plus rule metadata (id, title, Sigma
``level``/``status``, tags) and the matched module. Pure, no I/O.
"""

from datetime import datetime

from sigma.rule import SigmaRule

from sysdiagnose.sigmascan.loader import LoadedRule
from sysdiagnose.utils.base import Event


def _level_str(rule: SigmaRule) -> str:
    """Return the Sigma ``level`` as a lowercase string (e.g. ``"critical"``), or ``""``."""
    return rule.level.name.lower() if rule.level is not None else ""


def _status_str(rule: SigmaRule) -> str:
    """Return the Sigma ``status`` as a lowercase string (e.g. ``"experimental"``), or ``""``."""
    return rule.status.name.lower() if rule.status is not None else ""


def _tags(rule: SigmaRule) -> list[str]:
    """Return the rule's tags as plain strings."""
    return [str(t) for t in (rule.tags or [])]


def _event_datetime(event: dict) -> datetime:
    """Best-effort extraction of the matched event's datetime for the alert timestamp.

    Falls back to ``now`` (UTC) if the event has no parseable ``datetime`` — the alert still
    carries the full event, so no information is lost; only the alert's own timestamp field
    is approximate in that edge case.
    """
    raw = event.get("datetime") if isinstance(event, dict) else None
    if isinstance(raw, str):
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            pass
    return datetime.now().astimezone()


def build_alert(loaded_rule: LoadedRule, event: dict, matched_module: str) -> dict:
    """Build one alert dict for a rule match against ``event`` in ``matched_module``.

    The full matched event is embedded under ``data.event``; the result is a SAF event dict
    ready to write to ``sigmascan.jsonl``. No ``case_id`` is carried — the case is implicit
    from the output folder, and downstream ingestion adds it.
    """
    rule = loaded_rule.rule
    alert = Event(
        datetime=_event_datetime(event),
        message=f"ALERT: {rule.title or loaded_rule.id}",
        module="sigmascan",
        timestamp_desc="sigmascan match datetime (from matched event)",
        data={
            "rule_id": loaded_rule.id,
            "rule_title": rule.title or "",
            "level": _level_str(rule),
            "status": _status_str(rule),
            "matched_module": matched_module,
            "event": event,
            "tags": _tags(rule),
        },
    )
    return alert.to_dict()
