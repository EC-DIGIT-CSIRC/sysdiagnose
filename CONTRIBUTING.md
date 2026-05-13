# Contributing to Sysdiagnose Analysis Framework

Thank you for your interest in contributing to SAF! This document will help you get started.

## Getting Started

1. Fork the repository
2. Create a virtual environment and install dependencies (see [README.md](README.md#installation))
3. Read the [Developer Guidelines](docs/developer_guidelines.md) before writing code

## Developer Guidelines

All parsers and analysers must follow the conventions documented in [`docs/developer_guidelines.md`](docs/developer_guidelines.md). This includes:

- Architecture and method lifecycle
- How to implement `execute()` and `get_log_files()`
- Error handling (guard against missing files, use `logger.warning()`)
- Output format conventions
- Test structure with `skipTest` for missing data
- Result summary mechanics

## Pull Request Checklist

Before submitting a PR, verify:

- [ ] Class inherits from `BaseParserInterface` or `BaseAnalyserInterface`
- [ ] `description` class attribute is set
- [ ] `format` class attribute matches the return type of `execute()`
- [ ] `get_log_files()` returns only files that exist (parsers only)
- [ ] `execute()` guards against empty `get_log_files()` with `logger.warning()` + empty return
- [ ] No `IndexError` can propagate from `get_log_files()[0]` access
- [ ] No `print()` statements (enforced by ruff `T201`)
- [ ] Test file exists under `tests/` with `skipTest` guard for missing data
- [ ] Output validates correctly with test data
- [ ] All existing tests pass

## Running Tests

```bash
python -m unittest discover tests/
```

## Code Style

- Follow existing code patterns in the repository
- Use type hints
- Keep `execute()` focused on parsing logic — let the base class handle I/O and summary tracking
- Prefer `logger.warning()` over raising exceptions for expected conditions (missing files, empty data)

## Reporting Issues

When reporting bugs, please include:
- iOS version of the sysdiagnose archive
- Python version
- Full traceback
- Minimal reproduction steps

## Licence

By contributing, you agree that your contributions will be licensed under the [European Union Public Licence](https://commission.europa.eu/content/european-union-public-licence_en).
