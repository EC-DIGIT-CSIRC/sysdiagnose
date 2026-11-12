# `sigmascan` Rule Format

This document is the analyst-facing reference for writing detection rules for the
`sysdiagnose` **`sigmascan`** analyser. You should be able to write a valid rule from this
document alone.

`sigmascan` loads **Sigma-shaped YAML rules** and evaluates them against the parsed event
stream of a case (the `parsed_data/<module>` outputs of SAF parsers **and** analysers),
emitting one alert per match. It is a pre-Splunk, automated first-triage layer — a structured
successor to `yarascan`.

> **Rules are parsed and validated with [pySigma](https://github.com/SigmaHQ/pySigma).**
> `sigmascan` uses pySigma only as the rule parser/validator and provides its own matcher
> over SAF's nested events. It does **not** use pySigma's query backends. This means your
> rules are, and should stay, valid Sigma.

---

## 1. Where rules live

- Rules are loaded from a rules directory, recursively.
- Default directory: `./sigma` (relative to the working directory), overridable with the
  `SYSDIAGNOSE_SIGMA_RULES_PATH` environment variable — exactly like `yarascan`'s
  `./yara` / `SYSDIAGNOSE_YARA_RULES_PATH`.
- Every `*.yml` and `*.yaml` file under the rules root is loaded, including subdirectories,
  so you can organise rules into folders by objective.
- **Filename convention:** a descriptive slug, e.g. `darksword_implant_tags.yml`. The
  filename and `title` are how humans identify a rule day-to-day; the `id` is a UUID
  (see below).

**One rule per file.** Each YAML file contains a single Sigma rule.

---

## 2. Rule anatomy

A rule is a YAML document with three parts: **metadata**, **`logsource`**, and
**`detection`**.

```yaml
title: DarkSword implant unified-log tags      # metadata
id: 2f1b0c9a-7d4e-4a1b-9c2d-0e1f2a3b4c5d
status: experimental
level: critical
description: DarkSword in-memory implant log tags recovered by iVerify.
references:
  - https://iverify.io/blog/darksword-ios-exploit-kit-explained
author: csirc
tags:
  - attack.execution

logsource:                                      # scope (which modules to scan)
  product: ios

detection:                                      # what to match
  keywords:
    - "DarkSword-WIFI-DUMP"
    - "MIG_FILTER_BYPASS"
    - "TASKROP"
  condition: keywords
```

### 2.1 Metadata fields

| Field | Required | Notes |
|---|---|---|
| `title` | yes | Human-readable name. Shown in alerts. |
| `id` | yes | **UUID** (Sigma convention). Stable identity across renames. Generate one per rule (e.g. `uuidgen`). |
| `status` | recommended | Rule **maturity** — Sigma vocabulary (see below). |
| `level` | recommended | Match **severity** — Sigma vocabulary (see below). |
| `description` | recommended | Free text. What the rule detects and why. |
| `references` | optional | List of URLs / sources. |
| `author` | optional | Who wrote it. |
| `tags` | optional | Free-form tags, e.g. MITRE ATT&CK (`attack.execution`). Carried into the alert. |

There is **no `severity` key and no `state` key** — use `level` and `status`.

**`level`** — severity of a match. Sigma vocabulary:

```
informational | low | medium | high | critical
```

**`status`** — maturity/confidence of the rule itself. Sigma vocabulary:

```
stable | test | experimental | deprecated | unsupported
```

`status` is metadata only — it does **not** gate execution. Every loaded rule runs
regardless of its `status`.

### 2.2 `logsource` — which modules a rule scans

**Every rule must have a `logsource` block.** pySigma rejects a rule with no `logsource`,
so the minimum is:

```yaml
logsource:
  product: ios
```

`product: ios` is always present (our only product). Scoping to specific modules is done
with an **optional custom `modules` list** under `logsource`:

| `logsource` shape | Meaning |
|---|---|
| `logsource: {product: ios}` (no `modules`) | **All modules** — the rule is scanned against every module present in the case. |
| `logsource: {product: ios, modules: [crashlogs]}` | Only the `crashlogs` module. |
| `logsource: {product: ios, modules: [crashlogs, logarchive]}` | Only `crashlogs` and `logarchive`. |

- **A "module"** is a SAF output produced by a **parser** (e.g. `crashlogs`, `logarchive`)
  or an **analyser** (e.g. `apps`, `ps_everywhere`) that writes an **event stream**
  (`.jsonl` or `.json`). This lets rules target higher-level analyser findings, not just raw
  parser events.
- **Only event-stream, non-scanner modules are scannable.** Modules whose output is text or
  a visualization (e.g. `coverage`/html, `ps_matrix`/txt, `wifi_geolocation`/gpx) are not
  scannable, and neither are the scanners themselves (`sigmascan`, `yarascan`) — their
  output is findings, not a data source. A rule scoping to one of these is treated like an
  unknown module (below).
- Each name in `modules` must resolve to a **known, scannable parser or analyser** (parser
  checked first, then analyser). An unknown or non-scannable name is dropped and logged as
  an error, and the rule still runs against its remaining valid modules; the whole rule is
  skipped only if every listed module is unusable. The rest of the rule set always loads.
- A module that *is* known but produced **no output for this case** is a quiet no-op (no
  alert, no error).
- Use an **all-modules** rule for whole-event full-text / network-IOC string matching.
  Use a **module-scoped** rule when you match specific `data.*` fields whose shape belongs
  to one module.

> `modules` is a SAF-specific extension to Sigma's `logsource`. Standard Sigma `logsource`
> is single-valued (`category`/`product`/`service`), so there is no native way to list
> several sources in one rule. pySigma preserves our `modules` key in
> `logsource.custom_attributes`, and `sigmascan` reads it from there. A future Sigma export
> would fan a multi-module rule out into one rule per module.

### 2.3 `detection` — what to match

The `detection` block holds one or more **search identifiers** plus a **`condition`** that
combines them. Two kinds of search identifier are supported:

#### a) `keywords` — whole-event full-text

A `keywords` list is an **OR of substrings** matched over the **whole event's serialized
VALUES** (every leaf value in the event, joined — never field names or JSON punctuation).
This catches a term anywhere in the event, including deep inside `data.*`.

```yaml
detection:
  keywords:
    - "DarkSword-WIFI-DUMP"
    - "com.blue.test"
  condition: keywords
```

- Plain substring match, no tokenization. `TASKROP` matches inside `[TASKROP]` naturally.
- **Case-insensitive by default** (see §3).
- This is the surface for **network IOCs** in v1 — domains, IPs, and hashes are matched as
  plain strings over the event text (there is no network-field modelling yet).

#### b) Named selections — field matching

A named selection (any name, e.g. `sel_proc`) is a map of `field: value` pairs. Fields are
referenced by **dotted path** into the event (see §4). A map with several entries is an
**AND** of its conditions.

```yaml
detection:
  sel_proc:
    data.app_name:                 # list of values = "equals any of" (OR)
      - configd
      - wifid
      - securityd
    data.report.exception.type|contains: EXC_GUARD   # |contains modifier
  condition: sel_proc
```

- A **bare value** (`field: value`) is an exact match.
- A **list of values** (`field: [a, b]`) means "equals any of" (OR over the values).
- A **modifier** is appended with `|` (`field|contains: ...`). Supported modifiers in §3.

### 2.4 `condition` — combining selections

`condition` is a standard Sigma condition string, parsed by pySigma. Supported grammar:

- `and`, `or`, `not`
- parentheses for grouping
- `1 of sel_*` / `all of sel_*` (wildcard over selection names)
- `1 of them` / `all of them`

```yaml
detection:
  sel_proc: { data.app_name: [configd, wifid] }
  sel_exc:  { data.report.exception.type|contains: EXC_GUARD }
  condition: sel_proc and sel_exc
```

---

## 3. Operators and case handling

Field matches use Sigma field modifiers. **v1 supports this allow-list only:**

| Form | Meaning | Example |
|---|---|---|
| exact | exact match | `field: value` |
| value list | equals any of | `field: [a, b]` |
| `\|contains` | substring | `field\|contains: EXC_GUARD` |
| `\|startswith` | prefix | `field\|startswith: com.` |
| `\|endswith` | suffix | `field\|endswith: .dylib` |
| `\|cased` | force case-sensitive (chainable) | `field\|cased`, `field\|cased\|contains` |
| `keywords` | substring over whole event | (see §2.3a) |

**Case handling (follows Sigma):** matching is **case-insensitive by default**, for both
field operators and `keywords`. Add the **`cased`** modifier to force case-sensitive
matching. `cased` is chainable, e.g. `data.path|cased|contains`.

### Wildcards (`*` and `?`)

Glob wildcards work in field values **and** keywords, following Sigma semantics:

| Wildcard | Matches |
|---|---|
| `*` | any run of characters (including none) |
| `?` | exactly one character |

```yaml
detection:
  sel:
    data.path: "*/MobileSoftwareUpdate/*"     # any path containing that segment
    data.bundle_id|startswith: "com.apple.?"  # com.apple. + exactly one char
  condition: sel
```

- A value with no wildcard uses a fast plain string comparison; a value with a wildcard is
  matched as an (anchored) pattern. Anchoring follows the operator: a bare value is a full
  match (`foo*bar` ⇒ starts with `foo`, ends with `bar`), `|contains` matches anywhere,
  `|startswith`/`|endswith` anchor one end.
- Wildcards combine with modifiers (`data.x|contains: "a*b"`) and with `cased`.
- **To match a literal `*` or `?`, escape it:** `\*` / `\?` (Sigma convention). An escaped
  wildcard is treated as an ordinary character.
- All other regex metacharacters in a value (`.`, `+`, `(`, ...) are matched **literally** —
  only `*` and `?` are special.

**Unsupported in v1** — a rule using any of these is logged as an error and **skipped**
(the run continues):

- `|re` (full regular expressions)
- `|base64`, `|base64offset`
- `|cidr`
- numeric comparison modifiers (`|lt`, `|gt`, ...)
- aggregation / correlation modifiers

pySigma will happily parse these; it is `sigmascan`'s allow-list that rejects them. Glob
wildcards (`*`/`?`) are supported; full regex (`|re`) is not.

---

## 4. Field resolution (dotted paths)

Fields are resolved against the SAF event dict by **splitting the name on `.` and walking
the nested dictionary**:

- Top-level fields: `datetime`, `message`, `timestamp_desc`, `module`.
- Nested data fields: `data.app_name`, `data.report.exception.type`, arbitrarily deep.

(Note: the event carries `datetime`, not a separate top-level `timestamp` field, so match
on `datetime`.)

```
data.report.exception.type  →  event["data"]["report"]["exception"]["type"]
```

Semantics:

1. **Missing field → no match** (never an error). If any intermediate key is absent, that
   condition simply does not match. For example, a summary-only crash with no
   `data.report.*` will not match an exception-signature clause.
2. **List-valued field → match if ANY element matches** the operator (Sigma convention).

> Wildcards (`*`/`?`) apply to field **values only**, never to field **names/paths** — a
> path segment is always matched literally (use `keywords` to search without a known path).

An SAF event always has this top-level shape:

```json
{
  "datetime": "2023-05-24T20:27:43.000000+00:00",
  "timestamp_desc": "crash time",
  "message": "human-readable summary",
  "module": "crashlogs",
  "data": { "...parser/analyser-specific nested fields..." }
}
```

---

## 5. What an alert looks like

One alert is emitted per matched event. Each alert embeds the **full matched event** and
carries rule + match metadata. Alerts are written to `parsed_data/sigmascan.jsonl` with
`module = sigmascan`:

```json
{
  "datetime": "<matched event datetime>",
  "message": "ALERT: DarkSword implant unified-log tags",
  "timestamp_desc": "sigmascan match datetime (from matched event)",
  "module": "sigmascan",
  "data": {
    "rule_id": "2f1b0c9a-7d4e-4a1b-9c2d-0e1f2a3b4c5d",
    "rule_title": "DarkSword implant unified-log tags",
    "level": "critical",
    "status": "experimental",
    "matched_module": "logarchive",
    "event": { "...the full matched source event..." },
    "tags": ["attack.execution"]
  }
}
```

Zero matches produce an empty `sigmascan.jsonl` (no lines) — that is success, not an error.

---

## 6. Worked examples

### 6.1 Full-text keyword rule, all modules

Whole-event full-text terms, scanned against every module (`logsource` has no `modules`).
This is the shape for most ported text-matching rules and for network-IOC strings.

```yaml
title: DarkSword implant unified-log tags
id: 2f1b0c9a-7d4e-4a1b-9c2d-0e1f2a3b4c5d
status: experimental
level: critical
description: DarkSword in-memory implant log tags recovered by iVerify.
references:
  - https://iverify.io/blog/darksword-ios-exploit-kit-explained
author: csirc
tags:
  - attack.execution
logsource:
  product: ios                # no `modules` key -> ALL modules
detection:
  keywords:
    - "DarkSword-WIFI-DUMP"
    - "MIG_FILTER_BYPASS"
    - "TASKROP"
  condition: keywords
```

### 6.2 Field match scoped to a module

`logsource.modules` present → scanned only against those modules. Field matches use dotted
paths into nested `data.*` with Sigma modifiers.

```yaml
title: DarkSword daemon crash signature
id: 8c7d1e2f-3a4b-4c6d-8e8f-9a0b1c2d3e4f
status: test
level: high
logsource:
  product: ios
  modules:
    - crashlogs
detection:
  sel_proc:
    data.app_name:
      - configd
      - wifid
      - securityd
      - UserEventAgent
  sel_exc:
    data.report.exception.type|contains: EXC_GUARD
  condition: sel_proc and sel_exc
```

### 6.3 Network IOCs as full-text strings

No network fields in v1 — domains/IPs/hashes are plain substrings over the whole event.

```yaml
title: DarkSword network IOCs (string match)
id: a1b2c3d4-5e6f-4a7b-8c9d-0e1f2a3b4c5d
status: experimental
level: critical
description: >
  v1 limitation: matched as plain strings over the whole event JSON, not against
  modelled network fields.
logsource:
  product: ios                # no `modules` key -> ALL modules
detection:
  keywords:
    - "static.cdncounter.net"
    - "sqwas.shapelie.com"
    - "62.72.21.10"
  condition: keywords
```

---

## 7. Common mistakes (rule rejected / skipped)

A rejected rule is logged as an error naming the rule and the reason, then skipped; the rest
of the rule set still loads and the run continues.

- **No `logsource` block** → rejected by pySigma. Add at least `logsource: {product: ios}`.
- **Missing or non-UUID `id`** → rejected. Use a real UUID.
- **Missing `detection` / `condition`** → rejected.
- **Condition referencing an undefined selection** (e.g. `condition: sel` with no `sel`) →
  rejected.
- **Unsupported modifier** (`|re`, `|base64`, `|cidr`, numeric/aggregation) → rejected by
  the allow-list (§3).
- **Unknown or non-scannable module** in `logsource.modules` (not a known parser/analyser,
  or a text/visualization/scanner output — see §2.2) → the entry is dropped and logged as an
  error, and the rule still runs against its other valid modules. If *every* listed module
  is unusable, the whole rule is skipped.
- **Known module with no output for this case** → not an error; the rule is simply a no-op
  for that case.

> If **no** valid rules are found at all (empty rules directory, or every rule rejected),
> `sigmascan` logs a warning and produces no alerts — the run still succeeds.

---

## 8. Not supported in v1

These are deliberately out of scope for the first version:

- **Full regular expressions** (`|re`) and other modifiers outside the §3 allow-list.
  (Glob wildcards `*`/`?` *are* supported — see §3.)
- **Cross-event correlation** / stateful sequences (e.g. "N crashes within 5 minutes").
  Rules match a single event at a time.
- **Network-field modelling.** Network IOCs are string matches only (§6.3).
- **Per-rule iOS-version gating.** Every loaded rule runs regardless of the case's iOS
  version. (The analyser as a whole still respects SAF's `is_compatible()`.)
