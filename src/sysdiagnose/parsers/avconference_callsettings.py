#! /usr/bin/env python3

import glob
import os
from sysdiagnose.utils.base import BaseParserInterface
from datetime import datetime, timezone
import gzip
import re


class AvConferenceCallSettingsParser(BaseParserInterface):
    description = "Parsing AVConference CallSettings calldump files"
    format = "jsonl"  # by default json

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            "logs/AVConference/*-CallSettings.calldump.gz"
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            for item in glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)):
                if os.path.getsize(item) > 0:
                    log_files.append(item)
        return log_files

    def execute(self) -> list | dict:
        '''
        this is the function that will be called
        '''
        result = []
        log_files = self.get_log_files()
        for log_file in log_files:
            # ungzip the .gz file in memory
            with gzip.open(log_file, 'rb') as f:
                file_content = f.read()
                # process the uncompressed file using a separate function
                result.extend(self.parse_file_content(file_content, log_file))

        return result

    def parse_file_content(self, file_content: bytes, fname: str) -> list:
        # extract the start-timestamp from the filename
        entries = []

        entry_tpl = {}
        timestamp_m = re.search(r'([0-9]{8}-[0-9]{6})-', os.path.basename(fname))
        timestamp = datetime.strptime(timestamp_m.group(1), '%Y%m%d-%H%M%S')
        timestamp = timestamp.replace(tzinfo=timezone.utc)  # ensure timezone is UTC
        entry_tpl['datetime'] = timestamp.isoformat(timespec='microseconds')
        entry_tpl['timestamp'] = timestamp.timestamp()
        # parse the rest of the
        lines = file_content.decode().split('\n')
        for line in lines:
            entry = entry_tpl.copy()
            if re.match(r'^[0-9]{6}\.[0-9]{6} ', line):
                entry['message'] = line[13:].strip()
            else:
                entry['message'] = line.strip()
            entries.append(entry)
        return entries
