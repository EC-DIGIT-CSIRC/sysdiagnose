#! /usr/bin/env python3

import glob
import os
from sysdiagnose.utils.base import BaseParserInterface
from datetime import datetime, timezone
import csv


class BatteryBDCParser(BaseParserInterface):
    description = "Parsing BatteryBDC CSV files"
    format = "jsonl"  # by default json

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            "logs/BatteryBDC/*.csv"
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            for item in glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)):
                # skip files starting with a dot
                if os.path.basename(item).startswith('.'):
                    continue
                # keep non-empty files
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
            # load csv using csvdictreader and convert to json dict using the header
            # the field 'TimeStamp' is in the format '2021-09-01 00:00:00'
            # add a field that refers to the first part of the filename (before the timestamp)
            # add the usual fields: timestamp, datetime
            # add the entry to the results list
            with open(log_file, 'r') as f:
                reader = csv.DictReader(f)
                entry_type = os.path.basename(log_file).rsplit('_', maxsplit=2)[0]
                for row in reader:
                    row['type'] = entry_type
                    if 'TimeStamp' in row:
                        timestamp = datetime.strptime(row['TimeStamp'], '%Y-%m-%d %H:%M:%S')
                        timestamp = timestamp.replace(tzinfo=timezone.utc)  # ensure timezone is UTC
                        del row['TimeStamp']
                    elif 'set_system_time' in row:
                        timestamp = datetime.strptime(row['set_system_time'], '%Y-%m-%d %H:%M:%S %z')
                    else:
                        raise ValueError('No known timestamp field found in CSV file')
                    row['datetime'] = timestamp.isoformat(timespec='microseconds')
                    row['timestamp'] = timestamp.timestamp()
                    result.append(row)

        return result