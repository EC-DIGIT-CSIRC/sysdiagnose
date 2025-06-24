#! /usr/bin/env python3

# For Python3
# Script to print from Accessibility TCC logs
# Author: david@autopsit.org

import glob
import os
from sysdiagnose.utils.base import BaseParserInterface, logger
from sysdiagnose.utils.apollo import Apollo


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
            apollo = Apollo(logger=logger, os_version='yolo', saf_module=self.module_name)  # FIXME get right OS version, but also update the Apollo modules to be aware of the latest OS versions
            for logfile in self.get_log_files():
                result.extend(apollo.parse_db(db_fname=logfile, db_type='TCC.db'))
            return result

        except IndexError:
            return []
