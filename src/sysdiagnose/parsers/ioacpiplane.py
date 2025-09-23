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
        log_file = self.get_log_files()[0]
        data_tree = {}

        try:
            logger.info(f"Processing file {log_file}, new entry added", extra={'log_file': log_file})
            p = IORegStructParser()
            data_tree = p.parse(log_file)

        except Exception:
            logger.exception("IOACPIPlane parsing crashed")

        return data_tree
