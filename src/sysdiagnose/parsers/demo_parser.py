#! /usr/bin/env python3

import os
import json
from sysdiagnose.utils.base import BaseParserInterface, logger


class DemoParser(BaseParserInterface):
    description = "Demo parsers"
    format = "jsonl"  # by default json, use jsonl for event-based data

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files = [
            "demo_input_file.txt"
        ]
        return [os.path.join(self.case_data_subfolder, log_files) for log_files in log_files]

    def execute(self) -> list | dict:
        '''
        this is the function that will be called
        '''
        result = []
        log_files = self.get_log_files()
        for log_file in log_files:
            entry = {}

            # timestamp = datetime.strptime(item['timestamp'], '%Y-%m-%d %H:%M:%S.%f %z')
            # entry['datetime'] = timestamp.isoformat(timespec='microseconds')
            # entry['timestamp'] = timestamp.timestamp()
            result.append(entry)
            logger.info(f"Processing file {log_file}, new entry added", extra={'log_file': log_file, 'entry': entry})

         return result
