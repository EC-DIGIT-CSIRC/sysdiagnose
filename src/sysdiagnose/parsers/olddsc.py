#! /usr/bin/env python3

# For Python3
# Script to parse ./logs/olddsc files
# Author: david@autopsit.org
#
#
import glob
import os
from sysdiagnose.utils.misc import load_plist_file_as_json
from sysdiagnose.utils.base import BaseParserInterface


class OldDscParser(BaseParserInterface):
    description = "Parsing olddsc files"
    json_pretty = False

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> dict:
        log_files_globs = [
            'logs/olddsc/*'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        for log_file in self.get_log_files():
            return OldDscParser.parse_file(log_file)
        return {'error': ['No olddsc files present']}

    def parse_file(path: str) -> list | dict:
        try:
            return load_plist_file_as_json(path)
        except IndexError:
            return {'error': 'No olddsc file present'}
