#!/usr/bin/env python3
"""
Quick micro-benchmark for the sigmascan hot path.

Measures the per-event evaluation loop (`CompiledRule.evaluate` plus the once-per-event
keyword-value serialization) against synthetic events. This is NOT an end-to-end benchmark:
it uses synthetic events (no real parsed_data / logarchive), so treat the numbers as relative
indicators of hot-path cost, not absolute throughput on real cases.

Usage:
    python scripts/bench_sigmascan.py [n_events] [n_keyword_rules] [n_field_rules]
"""

import sys
import time

from sysdiagnose.sigmascan.condition import CompiledRule
from sysdiagnose.sigmascan.loader import load_rule_from_yaml
from sysdiagnose.sigmascan.matcher import serialize_event_values

HDR = "title: {title}\nid: {uuid}\nlogsource: {{product: ios}}\ndetection:\n"


def _uuid(i: int) -> str:
    return f"{i:08d}-0000-4000-8000-000000000000"


def make_keyword_rule(i: int):
    text = (
        HDR.format(title=f"kw{i}", uuid=_uuid(i))
        + f"  keywords:\n    - TERM_{i}\n    - OTHER_{i}\n  condition: keywords\n"
    )
    return load_rule_from_yaml(text, f"mem://kw{i}")


def make_field_rule(i: int):
    text = (
        HDR.format(title=f"fld{i}", uuid=_uuid(1_000_000 + i))
        + f"  sel:\n    data.app: name_{i}\n    data.lvl1.lvl2.tag|contains: SIG_{i}\n"
        + "  condition: sel\n"
    )
    return load_rule_from_yaml(text, f"mem://fld{i}")


def make_event(i: int) -> dict:
    """A moderately nested event, shaped loosely like a real SAF event."""
    return {
        "datetime": "2026-01-01T00:00:00.000000+00:00",
        "timestamp": 1767225600 + i,
        "timestamp_desc": "synthetic",
        "message": f"synthetic event number {i} with some descriptive text and a TERM_{i % 50} token",
        "module": "synthetic",
        "data": {
            "app": f"name_{i % 100}",
            "pid": i,
            "path": f"/some/path/to/binary_{i % 30}",
            "lvl1": {"lvl2": {"tag": f"payload SIG_{i % 40} embedded", "extra": "x" * 40}},
            "items": [f"item_{j}" for j in range(5)],
        },
    }


def bench(n_events: int, n_kw: int, n_fld: int) -> None:
    rules = [make_keyword_rule(i) for i in range(n_kw)] + [make_field_rule(i) for i in range(n_fld)]
    events = [make_event(i) for i in range(n_events)]
    n_rules = len(rules)

    print(f"events={n_events}  rules={n_rules} (keyword={n_kw}, field={n_fld})")
    print(f"evaluations = {n_events * n_rules:,}\n")

    # --- Stage 0: compile rules once (parse condition tree + value index) ---
    t0 = time.perf_counter()
    compiled = [CompiledRule(lr.rule) for lr in rules]
    t_compile = time.perf_counter() - t0
    print(f"compile rules:          {t_compile:.4f}s total  (once, not per event)")

    # --- Stage 1: keyword-value serialization only (once per event) ---
    t0 = time.perf_counter()
    blobs = [serialize_event_values(ev) for ev in events]
    t_ser = time.perf_counter() - t0
    print(f"serialize_event_values: {t_ser:.4f}s total  {t_ser / n_events * 1e6:.2f} us/event")

    # --- Stage 2: full evaluation loop (compiled rules, blob precomputed) ---
    matches = 0
    t0 = time.perf_counter()
    for ev, blob in zip(events, blobs, strict=True):
        for rule in compiled:
            if rule.evaluate(ev, event_values_text=blob):
                matches += 1
    t_eval = time.perf_counter() - t0

    total_evals = n_events * n_rules
    print(
        f"evaluate_rule loop:     {t_eval:.4f}s total  {t_eval / total_evals * 1e6:.2f} us/eval  ({matches:,} matches)"
    )

    eps = n_events / (t_ser + t_eval)
    print(f"\nthroughput: {eps:,.0f} events/sec  ({n_rules} rules each)  -> {eps * n_rules:,.0f} evals/sec")

    # Rough logarchive projection (order-of-magnitude only; synthetic data!)
    for scale in (1_000_000, 10_000_000):
        print(f"  projected {scale:,} events: ~{scale / eps:,.1f}s")


if __name__ == "__main__":
    n_events = int(sys.argv[1]) if len(sys.argv) > 1 else 20_000
    n_kw = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    n_fld = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    bench(n_events, n_kw, n_fld)
