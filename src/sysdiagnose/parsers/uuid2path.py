#! /usr/bin/env python3
"""
For Python3
Script to print the values from logs/tailspindb/UUIDToBinaryLocations (XML plist)
Uses Python3's plistlib
Author: cheeky4n6monkey@gmail.com

Change log: David DURVAUX - add function are more granular approach
"""

import glob
import os

from sysdiagnose.utils import misc
from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, logger


class UUID2PathParser(BaseParserInterface):
    description = "Parsing UUIDToBinaryLocations plist file"

    def __init__(self, config: SysdiagnoseConfig, case_id: str) -> None:
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = ["logs/tailspindb/UUIDToBinaryLocations"]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        log_files = self.get_log_files()
        if not log_files:
            logger.warning("No UUIDToBinaryLocations file present")
            return {}
        return misc.load_plist_file_as_json(log_files[0])
