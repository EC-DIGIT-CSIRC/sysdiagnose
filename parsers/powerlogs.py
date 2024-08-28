#! /usr/bin/env python3

# For Python3
# Script to print from powerlogs (last 3 days of logs)
# Author: david@autopsit.org

from utils import sqlite2json
import glob
import os
from utils.misc import merge_dicts
from utils.base import BaseParserInterface


class PowerLogsParser(BaseParserInterface):
    description = "Parsing powerlogs database"

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

    def execute(self) -> list | dict:
        result = {}
        for logfile in self.get_log_files():
            db_json = PowerLogsParser.parse_file(logfile)
            result = merge_dicts(result, db_json)  # merge both
        return result

    def parse_file(path: str) -> dict:
        return sqlite2json.sqlite2struct(path)
