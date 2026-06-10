# AI Agent Instructions for Sysdiagnose Analysis Framework

This file provides context for AI coding assistants working on this codebase.
Full developer documentation: `docs/developer_guidelines.md`

## Project Structure

```
src/sysdiagnose/
├── parsers/          # Parse raw sysdiagnose files into structured data
├── analysers/        # Process parsed data to produce insights
└── utils/
    ├── base.py       # BaseParserInterface, BaseAnalyserInterface, BaseInterface
    └── summary.py    # ResultSummary, ResultSummaryExecutionHandler, ResultSummaryFactory
tests/                # Unit tests (one per parser/analyser)
docs/                 # Documentation
```

## Architecture

- Parsers extend `BaseParserInterface`, analysers extend `BaseAnalyserInterface`
- Constructor signature: `def __init__(self, config: SysdiagnoseConfig, case: dict)`
  - `case` is the full case metadata dict (contains `case_id`, `ios_version`, `model`, etc.)
  - `self.case_id` is derived automatically from `case.get("case_id")`
- Only override `execute()` and `get_log_files()` (parsers) — the base class handles I/O, caching, and summary tracking
- Override `_write_result()` only for custom output formats (CSV, GPX, KML)
- Override `_load_output()` only for multi-file parsers

## iOS Version Compatibility

- Declare `ios_version = ">=17.0"` (PEP 440 specifier) on a parser/analyser class to restrict it to specific iOS versions
- Default is `ios_version = "*"` (all versions)
- `_execute_and_write()` automatically skips incompatible versions with `ExecutionStatus.SKIPPED`
- Use `self.is_compatible()` to check programmatically
- The `test_parsers_filestructure` and `test_analysers_filestructure` tests validate that all `ios_version` values are valid PEP 440 specifiers

## Key Rules

- Parsers: `execute()` must guard against missing files: check `get_log_files()` first, `logger.warning()` + return empty if none found
- Parsers: never let `IndexError` propagate from `get_log_files()[0]`
- Never raise exceptions for expected conditions (missing files, empty data, unsupported iOS versions)
- Use `logger` (not `print()`) — warnings/errors are captured by `ResultSummaryExecutionHandler`
- `print()` is enforced by ruff rule `T201` — only CLI entry points are exempt
- Return type must match `format`: json→dict/list, jsonl→list[dict] or Generator[dict], custom→str
- For jsonl, use `Event` dataclass and return `event.to_dict()`
- For large datasets (jsonl only), return a Generator to enable lazy streaming
- Analysers instantiate parsers using `ParserClass(self.config, self.case)` to pass through case metadata

## Tests

- Use `self.subTest(case_id=case_id, ios_version=_case.get('ios_version'))` when iterating over multiple cases so each case is reported independently
- Check compatibility first: `if not p.is_compatible(): self.skipTest(...)`
- Parsers: then check for log files: `if not files: self.fail(...)`
- Use `self.assert_has_required_fields_jsonl(item)` for jsonl validation
- Use `self.assert_result_summary_consistent(instance, result)` to validate summary matches output
- Call `save_result(force=True)` to ensure fresh execution

## Method Lifecycle

```
save_result() → _execute_and_write() → [is_compatible() check] → execute() + _write_result() + ResultSummaryExecutionHandler
```

If incompatible: `_execute_and_write()` returns empty result with `ExecutionStatus.SKIPPED`.

Outliers (custom I/O) use: `execute_with_result_summary()` → execute() + summary (no file write)

The persisted summary file (`<module>.summary.json`) has two purposes:

1. **Trust signal for cached data.** When loading from cache (CLI or API), the summary provides a glimpse of data quality (event count, errors, warnings, timing) without re-executing.
2. **Staleness detection (future).** The `start_time` field enables identifying outdated cached results — relevant for analysers depending on previously parsed data, since CLI logs only capture the current run.

## Do NOT

- Override `save_result()` unless absolutely necessary
- Catch broad `Exception` or `IndexError` to mask missing files
- Return `{"error": "..."}` for missing files — use `logger.warning()` + empty return instead
- Use `print()` for diagnostics — ruff `T201` will reject it
- Hold large datasets in memory when a Generator suffices
- Use `case_id` directly in constructors — always pass the full `case` dict
