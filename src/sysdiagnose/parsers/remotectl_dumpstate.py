#! /usr/bin/env python3
import glob
import os
from sysdiagnose.utils.tabbasedhierarchy import parse_tab_based_hierarchal_file, parse_block
from sysdiagnose.utils.base import BaseParserInterface


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
            for item in glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)):
                if os.path.getsize(item) > 0:
                    log_files.append(item)
        return log_files

    def execute(self) -> list | dict:
        try:
            return parse_tab_based_hierarchal_file(self.get_log_files()[0])
        except IndexError:
            return {'error': 'No remotectl_dumpstate.txt file present'}

    @staticmethod
    def parse_file(file_path: str) -> dict:
        """
        Parse the file and return a dictionary with the parsed data.
        """
        return parse_tab_based_hierarchal_file(file_path)

    @staticmethod
    def parse_file_content(file_content: str) -> dict:
        """
        Parse the file content and return a dictionary with the parsed data.
        """
        lines = file_content.splitlines()
        return parse_block(lines)
