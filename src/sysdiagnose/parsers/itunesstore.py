#! /usr/bin/env python3
"""
For Python3
Script to print from iTunes Store
Author: david@autopsit.org
"""

import glob
import os

from sysdiagnose.utils import misc, sqlite2json
from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, logger


class ITunesStoreParser(BaseParserInterface):
    description = "Parsing iTunes store logs"

    def __init__(self, config: SysdiagnoseConfig, case: dict) -> None:
        super().__init__(__file__, config, case)

    def get_log_files(self) -> list:
        log_files_globs = ["logs/itunesstored/downloads.*.sqlitedb"]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        log_files = self.get_log_files()
        if not log_files:
            logger.warning("No downloads.*.sqlitedb file found in logs/itunesstored/ directory")
            return {}
        return ITunesStoreParser.parse_file(log_files[0])

    @staticmethod
    def parse_file(path: str) -> list | dict:
        return misc.json_serializable(sqlite2json.sqlite2struct(path))
