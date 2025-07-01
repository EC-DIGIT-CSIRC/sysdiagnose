#! /usr/bin/env python3

# For Python3
# Script to print the values from logs/tailspindb/UUIDToBinaryLocations (XML plist)
# Uses Python3's plistlib
# Author: cheeky4n6monkey@gmail.com
#
# Change log: David DURVAUX - add function are more granular approach

import os
import glob
import sysdiagnose.utils.misc as misc
from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig


class UUID2PathParser(BaseParserInterface):
    description = "Parsing UUIDToBinaryLocations plist file"

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'logs/tailspindb/UUIDToBinaryLocations'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        try:
            return UUID2PathParser.parse_file(self.get_log_files()[0])
        except IndexError:
            return {'error': 'No UUIDToBinaryLocations file present'}

    def parse_file(path: str) -> list | dict:
        try:
            return misc.load_plist_file_as_json(path)
        except IndexError:
            return {'error': 'No UUIDToBinaryLocations file present'}

    def printResult(data):
        """
            Print the hashtable produced by getUUID2Path to console as UUID, path
        """
        if data:
            for uuid in data.keys():
                print(f"{str(uuid)}, {str(data[uuid])}")
        print(f"\n {str(len(data.keys()))} GUIDs found\n")
        return
