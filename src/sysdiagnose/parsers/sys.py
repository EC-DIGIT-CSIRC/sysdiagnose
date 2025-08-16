#! /usr/bin/env python3

# For Python3
# Script to print the values from /logs/SystemVersion/SystemVersion.plist
# Author: cheeky4n6monkey@gmail.com
#
# Change log: David DURVAUX - add function are more granular approach

import os
import glob
import sysdiagnose.utils.misc as misc
from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, logger, Event


class SystemVersionParser(BaseParserInterface):
    description = "Parsing SystemVersion plist file"
    format = 'jsonl'

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'logs/SystemVersion/SystemVersion.plist'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        try:
            entry = SystemVersionParser.parse_file(self.get_log_files()[0])
            timestamp = self.sysdiagnose_creation_datetime
            event = Event(
                datetime=timestamp,
                message=f"SystemVersion {entry.get('ProductName', '')} {entry.get('ProductVersion', '')} {entry.get('BuildVersion', '')}",
                module=self.module_name,
                timestamp_desc='sys at sysdiagnose creation',
                data=entry
            )
            return [event.to_dict()]
        except IndexError:
            logger.warning('No SystemVersion.plist file present')
            return []

    def parse_file(path: str) -> list | dict:
        return misc.load_plist_file_as_json(path)

    def parse_file_content(data: str) -> list | dict:
        """
        This function is used to parse the content of the file
        :param data: The content of the file
        :return: The parsed content
        """
        return misc.load_plist_string_as_json(data)
