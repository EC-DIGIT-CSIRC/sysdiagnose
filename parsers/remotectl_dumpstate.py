#! /usr/bin/env python3
import glob
import os
from utils.tabbasedhierarchy import parse_tab_based_hierarchal_file
from utils.base import BaseParserInterface


class RemotectlDumpstateParser(BaseParserInterface):
    description = "Parsing remotectl_dumpstate file containing system information"

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'remotectl_dumpstate.txt'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        try:
            return parse_tab_based_hierarchal_file(self.get_log_files()[0])
        except IndexError:
            return {'error': 'No remotectl_dumpstate.txt file present'}
