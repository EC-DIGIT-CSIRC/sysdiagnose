#! /usr/bin/env python3

# For Python3
# Script to extract the values from logs/Networking/com.apple.networkextension.plist
# Author: Emilien Le Jamtel


import sysdiagnose.utils.misc as misc
import os
import glob
from sysdiagnose.utils.base import BaseParserInterface


class NetworkExtensionParser(BaseParserInterface):
    description = "Parsing networkextension plist file"

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'logs/Networking/com.apple.networkextension.plist'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        return NetworkExtensionParser.parse_file(self.get_log_files()[0])

    def parse_file(path: str) -> list | dict:
        try:
            return misc.load_plist_file_as_json(path)
        except IndexError:
            return {'error': 'No com.apple.networkextension.plist file present'}
