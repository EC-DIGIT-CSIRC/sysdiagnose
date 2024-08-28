#! /usr/bin/env python3

# For Python3
# Script to print connection info from logs/appinstallation/AppUpdates.sqlite.db (iOS12)
# New version of iOS store data into logs/appinstallation/appstored.sqlitedb
# Author: david@autopsit.org

# PID: encoded in Litlle Endian??
# TODO - add support of iOS13...


from utils import sqlite2json
import glob
import os
import utils.misc as misc
from utils.base import BaseParserInterface


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
            return misc.json_serializable(sqlite2json.sqlite2struct(self.get_log_files()[0]))
        except IndexError:
            return {'error': 'No AppUpdates.sqlitedb or appstored.sqlitedb file found in logs/appinstallation/ directory'}
