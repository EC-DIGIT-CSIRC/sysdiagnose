#! /usr/bin/env python3

# For Python3
# Script to parse the swcutil_show.txt file
# Author: Emilien Le Jamtel

import glob
import os
from utils import multilinelog
from utils.base import BaseParserInterface


class MobileInstallationParser(BaseParserInterface):
    description = "Parsing mobile_installation logs file"

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'logs/MobileInstallation/mobile_installation.log*'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        result = []
        for logfile in self.get_log_files():
            result.extend(multilinelog.extract_from_file(logfile))
        return result
