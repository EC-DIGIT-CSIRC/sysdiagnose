#! /usr/bin/env python3

# For Python3
# Script to print from powerlogs (last 3 days of logs)
# Author: david@autopsit.org

from sysdiagnose.utils import sqlite2json
import glob
import os
from sysdiagnose.utils.base import BaseParserInterface
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class PowerLogsParser(BaseParserInterface):
    description = 'Parsing powerlogs database'
    json_pretty = False
    format = 'jsonl'

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        """
            Get the list of log files to be parsed
        """
        log_files_globs = [
            'logs/powerlogs/powerlog_*',
            'logs/powerlogs/log_*'  # LATER is this file of interest?
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list:
        result = []
        skipped = set()
        for logfile in self.get_log_files():
            db_json = PowerLogsParser.parse_file_to_json(logfile)
            for key, values in db_json.items():
                if 'sqlite_sequence' in key:
                    continue
                for value in values:
                    if 'timestamp' not in value:
                        skipped.add(key)
                        continue

                    try:
                        timestamp = datetime.fromtimestamp(value['timestamp'], tz=timezone.utc)
                        value['db_table'] = key
                        value['datetime'] = timestamp.isoformat(timespec='microseconds')
                        value['timestamp'] = timestamp.timestamp()
                        result.append(value)
                    except TypeError:
                        # skip "None" values and such
                        pass

        logger.warning("Skipped the following tables as there are not timestamps:")
        [logger.warning(f"  {table}") for table in skipped]
        return result

    def parse_file_to_json(path: str) -> dict:
        return sqlite2json.sqlite2struct(path)
