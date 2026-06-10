#! /usr/bin/env python3
import glob
import os

from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, logger
from sysdiagnose.utils.tabbasedhierarchy import parse_block, parse_tab_based_hierarchal_file


class RemotectlDumpstateParser(BaseParserInterface):
    description = "Parsing remotectl_dumpstate file containing system information"

    def __init__(self, config: SysdiagnoseConfig, case: dict) -> None:
        super().__init__(__file__, config, case)

    def get_log_files(self) -> list:
        log_files_globs = ["remotectl_dumpstate.txt"]
        log_files = []
        for log_files_glob in log_files_globs:
            for item in glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)):
                if os.path.getsize(item) > 0:
                    log_files.append(item)
        return log_files

    def execute(self) -> list | dict:
        log_files = self.get_log_files()
        if not log_files:
            logger.warning("No remotectl_dumpstate.txt file present")
            return {}
        return parse_tab_based_hierarchal_file(log_files[0])

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
