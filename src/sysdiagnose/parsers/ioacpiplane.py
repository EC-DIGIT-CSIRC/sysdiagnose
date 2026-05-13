#! /usr/bin/env python3

import os

from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, logger
from sysdiagnose.utils.ioreg_parsers.structure_parser import IORegStructParser


class IOACPIPlaneParser(BaseParserInterface):
    description = "IOACPIPlane.txt file parser"
    format = "json"

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_file = "ioreg/IOACPIPlane.txt"
        return [os.path.join(self.case_data_subfolder, log_file)]

    def execute(self) -> list | dict:
        log_files = self.get_log_files()
        if not log_files:
            logger.warning("No IOACPIPlane file present")
            return {}

        logger.info(f"Processing file {log_files[0]}, new entry added", extra={"log_file": log_files[0]})
        p = IORegStructParser()
        data_tree = p.parse(log_files[0])

        return data_tree
