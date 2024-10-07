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
from sysdiagnose.utils.base import BaseParserInterface
from datetime import datetime, timezone


class AppInstallationParser(BaseParserInterface):
    description = "Parsing app installation logs"

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
            db_json = misc.json_serializable(sqlite2json.sqlite2struct(self.get_log_files()[0]))
            skipped = set()
            for key, values in db_json.items():
                if 'sqlite_sequence' in key:
                    continue
                for value in values:
                    if 'timestamp' not in value:
                        skipped.add(key)
                        continue

                    try:
                        value['db_table'] = key
                        value['datetime'] = datetime.fromtimestamp(value['timestamp'], tz=timezone.utc).isoformat()
                        result.append(value)
                    except TypeError:
                        # skip "None" values and such
                        pass
            return result
        except IndexError:
            return []