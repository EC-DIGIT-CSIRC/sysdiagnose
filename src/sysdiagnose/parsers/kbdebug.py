#! /usr/bin/env python3

import glob
import os

from pyparsing import Regex, SkipTo, StringEnd

from sysdiagnose.utils.base import BaseParserInterface, Event, SysdiagnoseConfig, logger
from sysdiagnose.utils.times import parse_datetime


class KbdebugParser(BaseParserInterface):
    description = "kbdebug.txt logfile parser"
    format = "jsonl"  # by default json, use jsonl for event-based data
    ios_version = ">=12"

    def __init__(self, config: SysdiagnoseConfig, case: dict) -> None:
        super().__init__(__file__, config, case)

    def is_compatible(self) -> bool:
        version_compatibility = super().is_compatible()
        # not compatible with Apple TV
        device_compatibility = "AppleTV" not in self.case_model
        # both need to be compatible
        return version_compatibility and device_compatibility

    def get_log_files(self) -> list:
        log_files_globs = ["**/kbdebug.txt"]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_folder, log_files_glob), recursive=True))

        return log_files

    def execute(self) -> list | dict:
        fmt_timestamp = Regex(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \+\d{4}")
        fmt_level = Regex(r"\w+")
        fmt_line = (
            fmt_timestamp("timestamp")
            + ": "
            + fmt_level("level")
            + ": "
            + SkipTo(fmt_timestamp | StringEnd(), include=False)("message")
        )

        result = []
        log_files = self.get_log_files()
        for log_file in log_files:
            with open(log_file) as f:
                lines = f.read()
                for tokens, _start, _end in fmt_line.scanString(lines):
                    try:
                        timestamp = parse_datetime(str(tokens.timestamp), "%Y-%m-%d %H:%M:%S %z")
                        event = Event(
                            datetime=timestamp,
                            message=tokens.message,  # The rest of the kbdebug entry
                            module=self.module_name,
                            timestamp_desc="kbdebug event",
                            data={"level": tokens.level},
                        )
                        result.append(event.to_dict())
                    except Exception:
                        logger.exception("Failed to parse timestamp or create event")

        return result
