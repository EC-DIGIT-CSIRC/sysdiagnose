# Reference samples

| Sample | Purpose |
| --- | --- |
| `parsers/demo_parser.py` | Skeleton parser: reads a log file and emits a jsonl `Event`. |
| `analysers/demo_analyser.py` | Skeleton analyser: shows logging and returning a json result. |

## How to use one

1. Copy the file into the appropriate package folder, e.g.
   `cp docs/samples/parsers/demo_parser.py src/sysdiagnose/parsers/my_parser.py`
2. Rename the class (e.g. `DemoParser` -> `MyParser`).
3. Implement `get_log_files()` and `execute()` (parsers) or `execute()` (analysers).
4. The module is now auto-discovered — verify with `saf list parsers` / `saf list analysers`.

See [`docs/developer_guidelines.md`](../developer_guidelines.md) for the full
parser/analyser contract.
