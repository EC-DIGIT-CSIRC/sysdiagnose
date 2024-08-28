#! /usr/bin/env python3

# For Python3
# Script to print from Accessibility TCC logs
# Author: david@autopsit.org

from utils import sqlite2json
import glob
import os
import utils.misc as misc
from utils.base import BaseParserInterface


class AccessibilityTccParser(BaseParserInterface):
    description = "Parsing Accessibility TCC logs"

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
            return misc.json_serializable(sqlite2json.sqlite2struct(self.get_log_files()[0]))
        except IndexError:
            return {'error': 'No TCC.db file found in logs/Accessibility/ directory'}
