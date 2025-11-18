#! /usr/bin/env python3

import os
from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, logger, Event
from pyparsing import Regex, SkipTo, StringEnd

from datetime import datetime


class KbdebugParser(BaseParserInterface):
    description = "kbdebug.txt logfile parser"
    format = "jsonl"  # by default json, use jsonl for event-based data

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files = [
            "kbdebug.txt"
        ]
        return [os.path.join(self.case_data_subfolder, log_files) for log_files in log_files]

    def execute(self) -> list | dict:
        fmt_timestamp = Regex(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \+\d{4}")
        fmt_level = Regex(r"\w+")
        fmt_line = fmt_timestamp("timestamp") + ": " + fmt_level("level") + ": " + SkipTo(fmt_timestamp | StringEnd(), include=False)("message")

        result = []
        log_files = self.get_log_files()
        for log_file in log_files:
            with open(log_file, 'r') as f:
                lines = f.read()
                for tokens, _start, _end in fmt_line.scanString(lines):
                    # print(f"Timestamp: {tokens.timestamp}")
                    # print(f"Level: {tokens.level}")
                    # print(f"Message: {tokens.message}")
                    try:
                        timestamp = datetime.strptime(tokens.timestamp, '%Y-%m-%d %H:%M:%S %z')
                        event = Event(
                            datetime=timestamp,
                            message=tokens.message,  # The rest of the kbdebug entry
                            module=self.module_name,
                            timestamp_desc='kbdebug event',
                            data={
                                "level": tokens.level
                            }
                        )
                        result.append(event.to_dict())
                    except Exception:
                        logger.exception("Failed to parse timestamp or create event")

        return result
