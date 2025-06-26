#! /usr/bin/env python3
# For Python3
# Script to parse logdata_statistics_*.txt to ease parsing
# Author: roman@envoid.com
#

import glob
import json
import os
from datetime import datetime, timezone

from sysdiagnose.utils.base import BaseParserInterface, logger, Event


class LogDataStatisticsParser(BaseParserInterface):
    """
    A parser for JSONL log files matching `logdata.statistics.*.jsonl`.

    This parser extracts process information from system logs, specifically:
    - The `unixTime` field (converted to timestamp and human-readable datetime).
    - The `processList` containing process paths.
    """
    description = 'Parsing logdata.statistics.jsonl files'
    format = 'jsonl'

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        """
       Retrieves all `logdata.statistics.*.jsonl` log files in the archive.

       :return: A list of file paths matching the pattern.
       """
        log_files_globs = [
            'system_logs.logarchive/Extra/logdata.statistics.*.jsonl'
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
        Parses a given JSONL log file and extracts relevant process data.

        :path: File path to the log file.

        :return: A list of parsed process entries.
        """
        output = []

        try:
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as e:
                        logger.error(f'Error parsing JSON in file {path}: {e}')
                        continue

                    try:
                        timestamp = datetime.fromtimestamp(record.get('unixTime'), tz=timezone.utc)
                    except Exception:
                        logger.warning(f'No unixTime found in record in file {path}')
                        continue

                    # Iterate over each process in processList and create an output record
                    for proc in record.get('processList', []):
                        event = Event(
                            datetime=timestamp,
                            message=f"Logd {record['type']} while {proc['process']} is running",
                            module=self.module_name,
                            timestamp_desc=f"Logd {record['type']}",
                            data={
                                'process': proc['process'],
                                'file': record['file']
                            }
                        )
                        output.append(event.to_dict())
        except Exception as err:
            logger.error(f'Error parsing file {path}: {err}')

        return output
