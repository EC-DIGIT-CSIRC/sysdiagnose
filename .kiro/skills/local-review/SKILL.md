---
name: local-review
description: Review COMMITTED changes on the current branch against the 'main' branch, for branch/PR-level review. For uncommitted working-tree changes before a commit, use check-git-diff instead.
---

Run:

- `git diff --name-only HEAD` - if there are any staged or unstaged changes, show them and stop.
- `git --no-pager log -p origin/main..HEAD ':(exclude)*.svg'`

Then act as a Senior Software Engineer and evaluate based on industry best practices, including:

- Logic & Correctness: Does the code actually do what it's supposed to? Are there any obvious edge cases or 'off-by-one' errors?
- Clean Code & Readability: Is the naming intuitive? Are functions small and focused (Single Responsibility Principle)?
- Maintainability: Are there any 'code smells' like hard-coded strings, deep nesting, or duplicated logic (DRY)?
- Performance & Security: Are there inefficient loops, unnecessary API calls, or potential security vulnerabilities (e.g., exposed secrets)?
- Testing & Documentation: Are there corresponding unit tests? Is the code self-documenting, or are comments used where logic is non-obvious?
- Commits: Are the commits atomic? Do the commit messages correctly explain the changes made?

If Python files have changed:

- Make sure the Python is modern, idiomatic, and uses type annotations.
- Run the linter and formatter check: `ruff check` and `ruff format --check`. Fold any findings into the review (`print()` is rejected by rule `T201` outside CLI entry points — use `logger` instead).
- Offer to run the unit tests with `make test` (which runs `python -m pytest --verbose tests`), or a targeted subset such as `python -m pytest tests/test_parsers_<name>.py`. Run them if the user agrees, and fold the results into the review.

If a parser or analyser changed (anything under `src/sysdiagnose/parsers/` or `src/sysdiagnose/analysers/`), check it against the framework conventions in `AGENTS.md`:

- Parsers extend `BaseParserInterface`, analysers extend `BaseAnalyserInterface`; only `execute()` and `get_log_files()` should normally be overridden.
- Constructor signature is `def __init__(self, config: SysdiagnoseConfig, case: dict)` — the full `case` dict is passed through, never `case_id` directly.
- `execute()` must guard against missing files (check `get_log_files()` first, `logger.warning()` + return empty if none). Never let `IndexError` propagate from `get_log_files()[0]`, never catch broad `Exception`/`IndexError` to mask missing files, and never raise for expected conditions (missing files, empty data, unsupported iOS versions) or return `{"error": ...}` for them.
- Return type must match `format`: json→dict/list, jsonl→list[dict] or `Generator[dict]`, custom→str. For jsonl use the `Event` dataclass and return `event.to_dict()`; prefer a Generator for large datasets rather than holding them in memory.
- `ios_version` (if set) must be a valid PEP 440 specifier.
- A new parser/analyser should ship a matching test under `tests/`, following the patterns in `AGENTS.md` (subTest per case, compatibility check first, `assert_result_summary_consistent`, `save_result(force=True)`).

Compatibility risks (cached data and cross-version support):

The framework parses sysdiagnose archives across many iOS versions (13 through 26) and
caches parsed output plus a `<module>.summary.json` trust signal per case. Flag any
change that could break reading older archives or invalidate cached results as a
"Compatibility risk" in the output, naming the affected area and a mitigation. Common
cases: output schema changes to a parser/analyser that downstream analysers or cached
consumers rely on; narrowing an `ios_version` specifier so previously supported archives
are now skipped; changes to the `Event` structure or `ResultSummary` format; and changes
to `BaseInterface` I/O, caching, or summary tracking that affect every module at once.

Output Format:
Provide a PR title and body, a list of 'Must-Fix' issues, a list of 'Compatibility risks' and a list of 'Optional Suggestions' for improvement.
If a section has no useful content, drop it.
Format the issues as MF1, MF2, CR1, OS1, OS2 for easy referencing.
