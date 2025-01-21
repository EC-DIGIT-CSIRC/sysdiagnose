#! /usr/bin/env python3

# For Python3
# Script to print the values from /logs/SystemVersion/SystemVersion.plist
# Author: cheeky4n6monkey@gmail.com
#
# Change log: David DURVAUX - add function are more granular approach

import os
import glob
import sysdiagnose.utils.misc as misc
from sysdiagnose.utils.base import BaseParserInterface, logger


class SystemVersionParser(BaseParserInterface):
    description = "Parsing SystemVersion plist file"
    format = 'jsonl'

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'logs/SystemVersion/SystemVersion.plist'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        try:
            entry = SystemVersionParser.parse_file(self.get_log_files()[0])
            timestamp = self.sysdiagnose_creation_datetime
            entry['timestamp_desc'] = 'sysdiagnose creation'
            entry['timestamp'] = timestamp.timestamp()
            entry['datetime'] = timestamp.isoformat(timespec='microseconds')
            return [entry]
        except IndexError:
            logger.warning('No SystemVersion.plist file present')
            return []

    def parse_file(path: str) -> list | dict:
        return misc.load_plist_file_as_json(path)
