#! /usr/bin/env python3

# ---------------------------------------------------------------------------
# REFERENCE SAMPLE — NOT part of the sysdiagnose package.
#
# This file is intentionally kept outside of `src/sysdiagnose/parsers/` so it
# is NOT discovered by the framework, exposed via the CLI, packaged in the
# wheel, or picked up by the test suite. It exists purely as a starting point
# for developers writing a new parser.
#
# To turn it into a real parser: copy it into `src/sysdiagnose/parsers/`,
# rename the class, and implement `get_log_files()` and `execute()`.
# See docs/developer_guidelines.md for the full contract.
# ---------------------------------------------------------------------------

import os
from datetime import datetime

from sysdiagnose.utils.base import BaseParserInterface, Event, SysdiagnoseConfig, logger


class DemoParser(BaseParserInterface):
    description = "Demo parser"
    format = "jsonl"  # by default json, use jsonl for event-based data
    # ios_version = ">=17.0"  # optional: PEP 440 specifier for compatible iOS versions (default: "*" = all)

    def __init__(self, config: SysdiagnoseConfig, case: dict):
        super().__init__(__file__, config, case)

    def get_log_files(self) -> list:
        log_files = ["demo_input_file.txt"]
        return [os.path.join(self.case_data_subfolder, f) for f in log_files]

    def execute(self) -> list | dict:
        """
        This is the function that will be called by the framework.
        """
        log_files = self.get_log_files()
        if not log_files:
            logger.warning("No log files found.")
            return []

        result = []
        for log_file in log_files:
            entry = {}
            try:
                timestamp = datetime.strptime("1980-01-01 12:34:56.001 +00:00", "%Y-%m-%d %H:%M:%S.%f %z")
                event = Event(
                    datetime=timestamp,
                    message=f"Demo event from {log_file}",
                    module=self.module_name,
                    timestamp_desc="Demo timestamp",
                )

                result.append(event.to_dict())
                logger.info(f"Processing file {log_file}, new entry added", extra={"log_file": log_file})
                logger.debug(f"Entry details {entry!s}", extra={"entry": str(entry)})
                if not entry:
                    logger.warning("Empty entry.")
            # Do not catch all exceptions in production code, this is just for demonstration purposes
            except Exception:
                logger.exception("This will log an error with the exception information")
        return result
