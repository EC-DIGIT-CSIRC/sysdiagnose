#! /usr/bin/env python3

# For Python3
# Script to print from powerlogs (last 3 days of logs)
# Author: david@autopsit.org

import glob
import os
from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, logger
from sysdiagnose.utils.apollo import Apollo


class PowerLogsParser(BaseParserInterface):
    description = 'Parsing powerlogs database'
    json_pretty = False
    format = 'jsonl'

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        """
            Get the list of log files to be parsed
        """
        log_files_globs = [
            'logs/powerlogs/powerlog_*',
            'logs/powerlogs/log_*'  # LATER is this file of interest?
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list:
        result = []
        apollo = Apollo(logger=logger, saf_module=self.module_name, os_version='yolo')  # FIXME get right OS version, but also update the Apollo modules to be aware of the latest OS versions
        for logfile in self.get_log_files():
            result.extend(apollo.parse_db(db_fname=logfile, db_type='CurrentPowerlog.PLSQL'))

        return result
