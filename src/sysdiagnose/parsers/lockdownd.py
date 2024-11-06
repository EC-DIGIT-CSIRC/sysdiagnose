#! /usr/bin/env python3
import glob
import os
from sysdiagnose.utils.base import BaseParserInterface
from datetime import datetime, timezone
import re


class LockdowndParser(BaseParserInterface):
    description = "Parsing lockdownd logs file"
    format = 'jsonl'

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'logs/MobileLockdown/lockdownd.log'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        for log_file in self.get_log_files():
            with open(log_file, 'r') as f:
                result = LockdowndParser.extract_from_list(f.readlines())
                return result
        return []

    def extract_from_list(lines: list) -> list:
        result = []
        i = 0
        while i < len(lines):
            # first check if next line is a continuation
            current_line = lines[i]
            while True:
                try:
                    match = re.match(r'(^.{24}) pid=(\d+) ', lines[i + 1])
                    if match:
                        # next line is a new entry, so proces current line
                        break
                    else:
                        # continuation, so need to merge current line with next line
                        current_line += lines[i + 1]
                        i += 1
                except IndexError:
                    # last line, so process current line
                    break

            # process rebuild current_line
            match = re.match(r'(^.{24}) pid=(\d+) ([^:]+): (.*)$', current_line, re.DOTALL)
            timestamp = datetime.strptime(match.group(1), '%m/%d/%y %H:%M:%S.%f')
            timestamp = timestamp.replace(tzinfo=timezone.utc)

            # LATER parse the json blob that can sometimes be in the message
            item = {
                'timestamp': timestamp.timestamp(),
                'datetime': timestamp.isoformat(timespec='microseconds'),
                'pid': int(match.group(2)),
                'event_type': match.group(3),
                'msg': match.group(4).strip()
            }
            result.append(item)

            i += 1
            pass
        return result
