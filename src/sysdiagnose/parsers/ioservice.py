#! /usr/bin/env python3

import os
from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, logger
from sysdiagnose.utils.ioreg_parsers.structure_parser import IORegStructParser


class IOServiceParser(BaseParserInterface):
    description = "IOService.txt file parser"
    format = "json"

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_file = "ioreg/IOService.txt"
        return [os.path.join(self.case_data_subfolder, log_file)]

    def execute(self) -> list | dict:
        """           IOService file notes

            # Regex for +-o starting at start of file -> 1213 results
            (\s|\|)*\+-o

            # Regex for ALL +-o - 1213 results
            \+-o

            So we know that the data doesn't contain the node identifier ('+-o')

        """  # noqa: W605

        log_files = self.get_log_files()
        data_tree = {}

        for log_file in log_files:
            try:
                logger.info(f"Processing file {log_file}, new entry added", extra={'log_file': log_file})
                p = IORegStructParser()
                data_tree = p.parse(log_file)

            except Exception:
                logger.exception("IOService parsing crashed")

        return data_tree
