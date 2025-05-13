#! /usr/bin/env python3
# For Python3
# Script to parse logdata_statistics_*.txt to ease parsing
# Author: roman@envoid.com
#

import glob
import os
import re
from datetime import datetime, timezone

from sysdiagnose.utils.base import BaseParserInterface, logger


class LogDataStatisticsTxtParser(BaseParserInterface):
    """
    A parser for log files matching `logdata.statistics.*.txt`.

    This parser extracts process information from system logs, specifically:
    - The `time` field (converted to timestamp and human-readable datetime).
    - The `procs` section containing process paths.
    """
    description = 'Parsing logdata.statistics.txt files'
    format = 'jsonl'

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        """
       Retrieves all `logdata.statistics.*.txt` log files in the archive.

       :return: A list of file paths matching the pattern.
       """
        log_files_globs = [
            'system_logs.logarchive/Extra/logdata.statistics.*.txt'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))
        return log_files

    def execute(self) -> list | dict:
        """
        Executes the parsing process for all matching log files.

        :return: The result of the execution.
        """
        output = []
        for logfile in self.get_log_files():
            output.extend(self.parse_file(logfile))
        return output

    def parse_file(self, path: str) -> list:
        """
        Parses a given log file and extracts relevant process data.

        :path: File path to the log file.

        :return: A list of parsed process entries.
        """
        output = []

        try:
            with open(path, 'r') as f:
                inside_statistics_record = False
                record_tpl = {}
                timestamp = None

                for line in f:
                    line = line.strip()

                    if line.startswith('--- !logd statistics record'):
                        inside_statistics_record = True
                        record_tpl = {}
                        timestamp = None  # Reset timestamp for each record
                        continue

                    # Detect end of record
                    if line.startswith('--- !'):
                        inside_statistics_record = False
                        continue

                    if inside_statistics_record:
                        # Extract timestamp (datetime) from 'time' field
                        if line.startswith('time  :'):
                            time_str = line.split(':', 1)[1].strip()
                            timestamp = self.parse_timestamp(time_str)
                            record_tpl['timestamp'] = timestamp.timestamp()
                            record_tpl['datetime'] = timestamp.isoformat(timespec='microseconds')
                            continue

                        if line.startswith('file  :'):
                            record_tpl['file'] = line.split(':', 1)[1].strip()

                        if line.startswith('type  :'):
                            record_tpl['type'] = line.split(':', 1)[1].strip()
                            continue

                        # Extract process data from 'procs' section
                        if line.startswith('- ['):
                            match = re.match(r'- \[\s*(\d+),\s*([\d.]+),\s*(.*)\s*\]', line)
                            if match:
                                process = match.group(3)  # Process path

                                if timestamp:
                                    record = record_tpl.copy()
                                    record['process'] = process.strip()
                                    record['saf_module'] = self.module_name
                                    record['timestamp_desc'] = record['type']
                                    record['message'] = f"{record['type']} while {record['process']} is running"
                                    output.append(record)
        except Exception as err:
            logger.error(f'Error parsing file {path}: {err}')

        return output

    @staticmethod
    def parse_timestamp(time_str: str) -> datetime | None:
        """
        Parses a timestamp string into a timezone-aware datetime.

        :time_str: Timestamp string from the log file.

        :return: A timezone-aware datetime object in UTC, or None if parsing fails.
        """
        try:
            return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S%z').astimezone(timezone.utc)
        except ValueError as e:
            logger.error(f'Failed to parse timestamp: {time_str} - {e}')
            return None
