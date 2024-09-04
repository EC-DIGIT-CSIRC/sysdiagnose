#! /usr/bin/env python3

# For Python3
# Script to print from Accessibility TCC logs
# Author: david@autopsit.org

from utils import sqlite2json
import glob
import os
import utils.misc as misc
from utils.base import BaseParserInterface
from datetime import datetime, timezone


class AccessibilityTccParser(BaseParserInterface):
    description = 'Parsing Accessibility TCC logs'
    format = 'jsonl'

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'logs/Accessibility/TCC.db'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        # only one file to parse
        try:
            result = []
            skipped = set()
            json_db = misc.json_serializable(sqlite2json.sqlite2struct(self.get_log_files()[0]))
            for key, values in json_db.items():
                if 'sqlite_sequence' in key:
                    continue
                for value in values:
                    if 'last_modified' not in value:
                        skipped.add(key)
                        continue

                    try:
                        value['db_table'] = key
                        value['datetime'] = datetime.fromtimestamp(value['last_modified'], tz=timezone.utc).isoformat()
                        value['timestamp'] = value['last_modified']
                        result.append(value)
                    except TypeError:
                        # skip "None" values and such
                        pass

            return result

        except IndexError:
            return []
