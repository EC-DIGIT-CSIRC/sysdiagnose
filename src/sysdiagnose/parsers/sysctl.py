#! /usr/bin/env python3

import glob
import os

from pyparsing import Word, alphanums, nums

from sysdiagnose.utils.base import BaseParserInterface, Event, SysdiagnoseConfig, logger


class SysctlParser(BaseParserInterface):
    description = "sysctl.txt logfile parser"
    format = "jsonl"  # by default json, use jsonl for event-based data

    fmt_field = Word(alphanums + "._")
    fmt_value = Word(nums)
    fmt_line = fmt_field("field") + ":" + fmt_value("value")

    def __init__(self, config: SysdiagnoseConfig, case: dict) -> None:
        super().__init__(__file__, config, case)

    def get_log_files(self) -> list:
        log_files_globs = ["sysctl.txt"]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        result = []
        log_files = self.get_log_files()
        for log_file in log_files:
            with open(log_file) as f:
                lines = f.read().splitlines()
                result.extend(self.parse_lines(lines, log_file=log_file))
        return result

    def parse_lines(self, lines: list, log_file="") -> list:
        result = []
        for lineno, line in enumerate(lines, start=1):
            try:
                tokens = self.fmt_line.parse_string(line, parse_all=True)
                timestamp = self.sysdiagnose_creation_datetime
                event = Event(
                    datetime=timestamp,
                    message=f"{tokens.field} : {tokens.value}",
                    module=self.module_name,
                    timestamp_desc="Setting at sysdiagnose creation",
                    data={
                        tokens.field: tokens.value  # type: ignore
                    },
                )
                result.append(event.to_dict())
            except Exception:
                logger.error(f"Failed to parse line {lineno} in {log_file}: {line}")

        return result
