#! /usr/bin/env python3

# For Python3
# Script to parse ./logs/olddsc files
# Author: david@autopsit.org
#
#
import glob
import os
from sysdiagnose.utils.misc import load_plist_file_as_json
from sysdiagnose.utils.base import BaseParserInterface, logger


class OldDscParser(BaseParserInterface):
    description = "Parsing olddsc (Dynamic Shared Cache) files"
    format = 'jsonl'

    json_pretty = False

    def __init__(self, config: dict, case_id: str):
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
        timestamp_dict = {}
        timestamp = self.sysdiagnose_creation_datetime
        timestamp_dict['timestamp'] = timestamp.timestamp()
        timestamp_dict['datetime'] = timestamp.isoformat(timespec='microseconds')
        timestamp_dict['timestamp_info'] = 'sysdiagnose creation'
        timestamp_dict['timestamp_desc'] = 'olddsc'
        timestamp_dict['saf_module'] = self.module_name

        entries = []
        # we're not doing anything with
        # - Unslid_Base_Address
        # - Cache_UUID_String
        # only acting on Binaries list
        for log_file in self.get_log_files():
            for entry in OldDscParser.parse_file(log_file).get('Binaries', []):
                entry.update(timestamp_dict)
                entry['message'] = f"olddsc {entry['Path']} {entry['UUID_String']}"
                entries.append(entry)
        if not entries:
            logger.warning('No olddsc files present')
        return entries

    def parse_file(path: str) -> list | dict:
        try:
            return load_plist_file_as_json(path)
        except IndexError:
            return {'error': 'No olddsc file present'}
