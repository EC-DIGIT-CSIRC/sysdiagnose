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
- Only override `execute()` and `get_log_files()` (parsers) — the base class handles I/O, caching, and summary tracking
- Override `_write_result()` only for custom output formats (CSV, GPX, KML)
- Override `_load_output()` only for multi-file parsers

## Key Rules

- `execute()` must guard against missing files: check `get_log_files()` first, `logger.warning()` + return empty if none found
- Never let `IndexError` propagate from `get_log_files()[0]`
- Never raise exceptions for expected conditions (missing files, empty data, unsupported iOS versions)
- Use `logger` (not `print()`) — warnings/errors are captured by `ResultSummaryExecutionHandler`
- `print()` is enforced by ruff rule `T201` — only CLI entry points are exempt
- Return type must match `format`: json→dict/list, jsonl→list[dict] or Generator[dict], custom→str
- For jsonl, use `Event` dataclass and return `event.to_dict()`
- For large datasets (jsonl only), return a Generator to enable lazy streaming

## Tests

- Always guard with `self.skipTest(f"No log files found for {case_id}")` when files are missing
- Use `self.assert_has_required_fields_jsonl(item)` for jsonl validation
- Use `self.assert_result_summary_consistent(instance, result)` to validate summary matches output
- Call `save_result(force=True)` to ensure fresh execution

## Method Lifecycle

```
save_result() → _execute_and_write() → execute() + _write_result() + ResultSummaryExecutionHandler
```

Outliers (custom I/O) use: `execute_with_result_summary()` → execute() + summary (no file write)

## Do NOT

- Override `save_result()` unless absolutely necessary
- Catch broad `Exception` or `IndexError` to mask missing files
- Return `{"error": "..."}` for missing files — use `logger.warning()` + empty return instead
- Use `print()` for diagnostics — ruff `T201` will reject it
- Hold large datasets in memory when a Generator suffices
