"""
Minimal parser fixture for the test suite.

Behaves exactly like the former ``demo_parser``: it emits a single jsonl event
and logs one warning, producing a summary with status WARNING, num_events=1,
num_warnings=1, num_errors=0.
"""

from datetime import datetime

from sysdiagnose.utils.base import BaseParserInterface, Event, SysdiagnoseConfig, logger


class SampleParser(BaseParserInterface):
    description = "Sample parser (test fixture)"
    format = "jsonl"
    # ios_version defaults to "*" (all versions) — required for the compatibility tests.

    def __init__(self, config: SysdiagnoseConfig, case: dict):
        super().__init__(__file__, config, case)

    def get_log_files(self) -> list:
        # A non-empty list keeps execute() on the happy path without touching disk.
        return ["sample_input_file.txt"]

    def execute(self) -> list | dict:
        log_files = self.get_log_files()
        if not log_files:
            logger.warning("No log files found.")
            return []

        result = []
        for log_file in log_files:
            timestamp = datetime.strptime("1980-01-01 12:34:56.001 +00:00", "%Y-%m-%d %H:%M:%S.%f %z")
            event = Event(
                datetime=timestamp,
                message=f"Sample event from {log_file}",
                module=self.module_name,
                timestamp_desc="Sample timestamp",
            )
            result.append(event.to_dict())
            logger.info(f"Processing file {log_file}, new entry added", extra={"log_file": log_file})
            logger.warning("Empty entry.")
        return result
