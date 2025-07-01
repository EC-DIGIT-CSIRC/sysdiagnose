#! /usr/bin/env python3

# For Python3
# Script to print from iTunes Store
# Author: david@autopsit.org

from sysdiagnose.utils import sqlite2json
import glob
import os
import sysdiagnose.utils.misc as misc
from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig


class iTunesStoreParser(BaseParserInterface):
    description = "Parsing iTunes store logs"

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'logs/itunesstored/downloads.*.sqlitedb'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        # there's only one file to parse
        try:
            return iTunesStoreParser.parse_file(self.get_log_files()[0])
        except IndexError:
            return {'error': 'No downloads.*.sqlitedb file found in logs/itunesstored/ directory'}

    def parse_file(path: str) -> list | dict:
        return misc.json_serializable(sqlite2json.sqlite2struct(path))
