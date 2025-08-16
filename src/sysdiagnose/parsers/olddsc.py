#! /usr/bin/env python3

# For Python3
# Script to parse ./logs/olddsc files
# Author: david@autopsit.org
#
#
import glob
import os
from sysdiagnose.utils.misc import load_plist_file_as_json
from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, logger, Event


class OldDscParser(BaseParserInterface):
    description = "Parsing olddsc (Dynamic Shared Cache) files"
    format = 'jsonl'

    json_pretty = False

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> dict:
        log_files_globs = [
            'logs/olddsc/*'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list:
        timestamp = self.sysdiagnose_creation_datetime

        entries = []
        # we're not doing anything with
        # - Unslid_Base_Address
        # - Cache_UUID_String
        # only acting on Binaries list
        for log_file in self.get_log_files():
            for entry in OldDscParser.parse_file(log_file).get('Binaries', []):
                event = Event(
                    datetime=timestamp,
                    message=f"olddsc {entry['Path']} {entry['UUID_String']}",
                    module=self.module_name,
                    timestamp_desc='olddsc',
                    data=entry
                )
                event.data['timestamp_info'] = 'sysdiagnose creation time'

                entries.append(event.to_dict())

        if not entries:
            logger.warning('No olddsc files present')
        return entries

    def parse_file(path: str) -> list | dict:
        try:
            return load_plist_file_as_json(path)
        except IndexError:
            return {'error': 'No olddsc file present'}
