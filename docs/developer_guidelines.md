# Developer Guidelines: Writing Parsers and Analysers

This document provides guidelines for developing new parsers and analysers within the Sysdiagnose Analysis Framework (SAF).

## Architecture Overview

```
BaseInterface (ABC)
├── BaseParserInterface    → Parses raw sysdiagnose files into structured data
└── BaseAnalyserInterface  → Processes parsed data to produce insights
```

The framework handles execution, file I/O, caching, iOS version compatibility, and result summary tracking automatically. Your job is to implement `execute()` and `get_log_files()` (parsers only).

### Constructor signature

All parsers and analysers use:

```python
def __init__(self, config: SysdiagnoseConfig, case: dict) -> None:
    super().__init__(__file__, config, case)
```

The `case` dict is the full case metadata from `cases.json` and contains keys like `case_id`, `ios_version`, `model`, `serial_number`, `date`, etc. The base class derives `self.case_id` from `case.get("case_id")` automatically.

### Key lifecycle methods (handled by the base class)

| Method | Role |
|--------|------|
| `save_result()` | Orchestrates: execute → write → summary |
| `_execute_and_write()` | Checks compatibility, calls `execute()`, writes via `_write_result()`, builds `ResultSummary` |
| `_write_result()` | Writes the result to the output file |
| `_load_output()` | Loads cached result from the output file |
| `get_result()` | Returns cached result or triggers `save_result()` |
| `get_result_summary()` | Returns the `ResultSummary` (loads from disk if needed) |
| `is_compatible()` | Checks if this parser/analyser supports the case's iOS version |

You should **not** override these unless you have a non-standard output format (see [Custom Output Formats](#custom-output-formats)).

## iOS Version Compatibility

Parsers and analysers can declare which iOS versions they support using a PEP 440 version specifier:

```python
class MyParser(BaseParserInterface):
    ios_version = ">=17.0"          # Only iOS 17 and above
    # ios_version = ">=14.0,<17.0"  # iOS 14 to 16 only
    # ios_version = "*"             # All versions (default)
```

The framework automatically skips execution for incompatible versions:
- `_execute_and_write()` checks `is_compatible()` before calling `execute()`
- Incompatible cases get an empty result and `ExecutionStatus.SKIPPED` in the summary
- No output file is written for skipped executions

You can also check compatibility programmatically:
```python
if not self.is_compatible():
    # Handle incompatibility
```

## Writing a Parser

### Minimal implementation

```python
import os
from sysdiagnose.utils.base import BaseParserInterface, Event, SysdiagnoseConfig, logger


class MyParser(BaseParserInterface):
    description = "Parsing my_file.txt"
    format = "jsonl"  # "json" for structured data, "jsonl" for event-based timelines
    # ios_version = ">=17.0"  # optional: PEP 440 specifier (default: "*" = all)

    def __init__(self, config: SysdiagnoseConfig, case: dict):
        super().__init__(__file__, config, case)

    def get_log_files(self) -> list:
        log_files_globs = ["my_file.txt"]
        return [
            os.path.join(self.case_data_subfolder, f)
            for f in log_files_globs
            if os.path.exists(os.path.join(self.case_data_subfolder, f))
        ]

    def execute(self) -> list:
        log_files = self.get_log_files()
        if not log_files:
            logger.warning("No my_file.txt file present")
            return []

        result = []
        for log_file in log_files:
            # Parse the file and build Event objects
            ...
        return result
```

### Rules for `execute()`

1. **Always guard against missing files.** Check `get_log_files()` at the start and return an empty result with `logger.warning()` if no files are found.

2. **Return type must match `format`:**
   - `format = "json"` → return `dict` or `list`
   - `format = "jsonl"` → return `list[dict]` or a `Generator[dict]`
   - Custom formats (e.g. `"csv"`, `"gpx"`) → return `str`

3. **Use `logger` for diagnostics**, not `print()`. The `ResultSummary` captures warning/error counts automatically:
   - `logger.warning(...)` → increments warning count, sets status to WARNING
   - `logger.error(...)` → increments error count, sets status to ERROR
   - `logger.info(...)` / `logger.debug(...)` → informational, no impact on status
   - `print()` is **forbidden** in parsers, analysers, and utilities — enforced by ruff rule `T201`. Only CLI entry points (`__main__.py`, `__init__.py`) are exempt.

4. **Never raise exceptions for expected conditions.** Missing files, empty data, or unsupported iOS versions are normal — log a warning and return empty. Only let exceptions propagate for genuine bugs.

5. **For `jsonl` format, use `Event` objects:**

```python
from datetime import datetime
from sysdiagnose.utils.base import Event

event = Event(
    datetime=timestamp,           # datetime object (timezone-aware)
    message="Human-readable description",
    module=self.module_name,
    timestamp_desc="What this timestamp represents",
    data={"key": "value"},        # Additional structured data
)
result.append(event.to_dict())
```

### Using Generators for large datasets (jsonl only)

If your parser produces a large number of events, you can return a `Generator` instead of a `list`. The framework will consume it lazily, writing each event to disk as it's yielded:

```python
from collections.abc import Generator

def execute(self) -> Generator[dict, None, None]:
    log_files = self.get_log_files()
    if not log_files:
        logger.warning("No files found")
        return

    for log_file in log_files:
        for entry in self._parse_file(log_file):
            yield entry
```

This is only supported for `format = "jsonl"`.

## Writing an Analyser

Analysers consume parsed data (from one or more parsers) and produce derived output.

### Minimal implementation

```python
from sysdiagnose.parsers.my_parser import MyParser
from sysdiagnose.utils.base import BaseAnalyserInterface, SysdiagnoseConfig, logger


class MyAnalyser(BaseAnalyserInterface):
    description = "Analyse something useful"
    format = "json"
    # ios_version = ">=17.0"  # optional: PEP 440 specifier (default: "*" = all)

    def __init__(self, config: SysdiagnoseConfig, case: dict):
        super().__init__(__file__, config, case)

    def execute(self) -> dict:
        parser = MyParser(self.config, self.case)
        data = parser.get_result()  # triggers parsing if not cached
        # Process data...
        return {"analysis": "result"}
```

### Rules for analysers

- Instantiate parsers with `ParserClass(self.config, self.case)` — this passes the full case metadata through.
- Call `parser.get_result()` to obtain input data — this handles caching automatically.
- Follow the same `execute()` rules as parsers regarding logging and return types.
- Analysers do not have `get_log_files()` — guard against empty input data from upstream parsers instead.
- For custom output formats (GPX, KML, CSV), return a `str` from `execute()` and set `format` accordingly.

## Custom Output Formats

If your output is not JSON/JSONL (e.g. CSV, GPX, KML), you have two options:

### Option A: Return a string (preferred)

Set `format` to your extension and return the serialized content as a `str` from `execute()`:

```python
class MyGpxAnalyser(BaseAnalyserInterface):
    format = "gpx"

    def execute(self) -> str:
        # Build and return the GPX XML as a string
        return gpx.to_xml()
```

The base class writes the string to `self.output_file` automatically.

### Option B: Override `_write_result` (for complex cases)

If you need custom serialization logic (e.g. CSV with dynamic headers):

```python
class MyCsvAnalyser(BaseAnalyserInterface):
    format = "csv"

    def execute(self) -> list:
        return [{"col1": "val1", "col2": "val2"}, ...]

    def _write_result(self, result, indent=None) -> int:
        self._result = result
        with open(self.output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=...)
            writer.writeheader()
            writer.writerows(self._result)
        return len(self._result)
```

**Important:** `_write_result` must:
- Assign `self._result = result` (or the materialized form)
- Return the number of events/entries written (used for the summary)

### Option C: Override `_load_output` (for multi-file parsers)

If your parser writes to multiple files instead of a single output file, override `_load_output()` to reconstruct the result from those files, and `output_exists()` to check for their presence:

```python
def output_exists(self) -> bool:
    return os.path.isdir(self.output_folder) and any(...)

def _write_result(self, result, indent=None) -> int:
    self._result = result
    for name, data in self._result.items():
        # Write each entry to a separate file
        ...
    return len(self._result)

def _load_output(self) -> dict:
    # Read from multiple files
    ...
```

## Writing Tests

### Test execution order

Tests are run via pytest (which discovers and runs `unittest.TestCase` subclasses). A `conftest.py` hook ensures parser tests run before analyser tests, so analysers benefit from cached parsed data:

```
tests/conftest.py  → reorders: test_parsers_* → other → test_analysers_*
```

This means analyser tests don't need to explicitly trigger their parser dependencies — the output will already exist from the parser test run.

### Parser test structure

```python
import os
import unittest

from sysdiagnose.parsers.my_parser import MyParser
from tests import SysdiagnoseTestCase


class TestParsersMyParser(SysdiagnoseTestCase):
    def test_parse(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                p = MyParser(self.sd.config, case=_case)
                if not p.is_compatible():
                    self.skipTest(f"Parser {p.module_name} not compatible with iOS {_case.get('ios_version')}")

                files = p.get_log_files()
                if not files:
                    self.fail(f"No log files found for {case_id}: parser {p.module_name}, iOS {_case.get('ios_version')}")

                p.save_result(force=True)
                self.assertTrue(os.path.isfile(p.output_file))

                result = p.get_result()
                self.assertGreater(len(result), 0)
                for item in result:
                    self.assert_has_required_fields_jsonl(item)
                self.assert_result_summary_consistent(p, result)


if __name__ == "__main__":
    unittest.main()
```

### Analyser test structure

```python
import os
import unittest

from sysdiagnose.analysers.my_analyser import MyAnalyser
from tests import SysdiagnoseTestCase


class TestAnalysersMyAnalyser(SysdiagnoseTestCase):
    def test_analyse(self):
        for case_id, _case in self.sd.cases().items():
            with self.subTest(case_id=case_id, ios_version=_case.get("ios_version")):
                a = MyAnalyser(self.sd.config, case=_case)
                if not a.is_compatible():
                    self.skipTest(f"Analyser {a.module_name} not compatible with iOS {_case.get('ios_version')}")

                a.save_result(force=True)
                self.assertTrue(os.path.isfile(a.output_file))

                result = a.get_result()
                self.assertGreater(len(result), 0)
                self.assert_result_summary_consistent(a, result)


if __name__ == "__main__":
    unittest.main()
```

### Test assertion helpers

The `SysdiagnoseTestCase` base class provides:

| Helper | Purpose |
|--------|---------|
| `assert_has_required_fields_jsonl(item)` | Validates that a jsonl entry has `datetime`, `message`, `timestamp_desc`, `module` |
| `assert_result_summary_consistent(instance, result)` | Validates summary matches output and **fails the test if execution produced errors** |
| `assert_result_summary_consistent(instance, result, allow_errors=True)` | Same validation but tolerates errors (use for parsers with known issues) |

### Test rules

1. **Use `self.subTest(case_id=case_id, ios_version=_case.get('ios_version'))`** when iterating over multiple cases so each case is reported independently.

2. **Check compatibility first:** `if not p.is_compatible(): self.skipTest(...)` — incompatible iOS versions are expected, not failures.

3. **Parsers: check for log files:** `if not files: self.fail(...)` — a compatible parser with missing files indicates a real problem.

4. **Use `self.assert_has_required_fields_jsonl(item)`** for jsonl parsers to validate the event structure.

5. **Use `self.assert_result_summary_consistent(instance, result)`** to validate that the `ResultSummary` matches the actual output. This will **fail the test if any errors occurred during execution** — use `allow_errors=True` only for parsers with known upstream issues.

6. **Call `save_result(force=True)`** to ensure the parser/analyser runs fresh.

7. **Validate the output file exists** after saving.

8. **Test with the provided test data** under `tests/testdata/`. Add new test archives if your parser targets files not present in existing test data.

## Result Summary

The framework automatically tracks execution metadata via `ResultSummary`:

- **status**: `ok`, `warning`, `error`, or `skipped` — derived from log handler counts and compatibility
- **start_time** / **duration**: execution timing (not set for `skipped`)
- **num_events**: number of entries produced
- **num_errors** / **num_warnings**: counts from `logger.error()` / `logger.warning()` calls during execution

You don't need to manage this manually — it's built by `ResultSummaryExecutionHandler` during `_execute_and_write()`. The summary is persisted as `<module_name>.summary.json` alongside the output file.

### Why the summary is persisted

The summary file serves as a sidecar metadata cache with two purposes:

1. **Trust signal for cached data.** When a consumer (CLI or API) loads results from cache rather than re-executing, the summary provides a glimpse of the data quality: how many events were produced, whether errors or warnings occurred, and when it was generated.

2. **Staleness detection (future).** The summary's `start_time` enables detection of outdated cached results — particularly relevant for the CLI when invoking analysers that depend on previously parsed data.

## Checklist for new parsers/analysers

- [ ] Class inherits from `BaseParserInterface` or `BaseAnalyserInterface`
- [ ] Constructor takes `(config: SysdiagnoseConfig, case: dict)` and calls `super().__init__(__file__, config, case)`
- [ ] `description` class attribute is set
- [ ] `format` class attribute matches the return type of `execute()`
- [ ] `ios_version` is set if the parser/analyser only supports specific iOS versions (valid PEP 440 specifier)
- [ ] `get_log_files()` returns only files that exist (parsers only)
- [ ] `execute()` guards against empty `get_log_files()` with `logger.warning()` + empty return (parsers only)
- [ ] Analysers instantiate parsers with `ParserClass(self.config, self.case)`
- [ ] No `print()` statements (enforced by ruff `T201`)
- [ ] Unit test uses `subTest`, `is_compatible()` check, and `assert_result_summary_consistent()`
- [ ] Output validates correctly with test data
