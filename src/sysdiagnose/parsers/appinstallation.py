#! /usr/bin/env python3

# For Python3
# Script to print connection info from logs/appinstallation/AppUpdates.sqlite.db (iOS12)
# New version of iOS store data into logs/appinstallation/appstored.sqlitedb
# Author: david@autopsit.org

# PID: encoded in Litlle Endian??


from sysdiagnose.utils import sqlite2json
import glob
import os
import sysdiagnose.utils.misc as misc
from sysdiagnose.utils.base import BaseParserInterface, logger
from datetime import datetime, timezone


class AppInstallationParser(BaseParserInterface):
    description = "Parsing app installation logs"
    format = 'jsonl'

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'logs/appinstallation/AppUpdates.sqlitedb',
            'logs/appinstallation/appstored.sqlitedb'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        try:
            result = []
            for filename in self.get_log_files():
                db_json = misc.json_serializable(sqlite2json.sqlite2struct(filename))
                skipped = set()
                for key, items in db_json.items():
                    if 'sqlite_sequence' in key:
                        continue
                    for item in items:
                        if 'timestamp' not in item:
                            skipped.add(key)
                            continue

                        try:
                            timestamp = datetime.fromtimestamp(item['timestamp'], tz=timezone.utc)
                            item['saf_db_table'] = key
                            item['datetime'] = timestamp.isoformat(timespec='microseconds')
                            item['timestamp'] = timestamp.timestamp()
                            item['saf_module'] = self.module_name
                            item['timestamp_desc'] = key
                            item['message'] = ''
                            result.append(item)
                        except TypeError:
                            # skip "None" values and such
                            pass
            return result
        except IndexError:
            logger.exception("Index error, returning empty list")
            return []
