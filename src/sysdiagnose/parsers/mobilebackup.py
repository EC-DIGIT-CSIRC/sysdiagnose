#! /usr/bin/env python3

import glob
import os
from sysdiagnose.utils.base import BaseParserInterface
from sysdiagnose.utils import misc
from datetime import datetime
import re


class MobileBackupParser(BaseParserInterface):
    description = "Parsing mobilebackup plist file"
    format = 'jsonl'

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'logs/MobileBackup/com.apple.MobileBackup.plist'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        result = []
        for logfile in self.get_log_files():
            json_data = misc.load_plist_file_as_json(logfile)
            # add LastOnConditionEvents that contain errors
            for i, event in enumerate(json_data.get('LastOnConditionEvents', [])):
                # "2023-02-22T10:24:49.051-08:00|158966.533|1|1|0|1|1|0|120|73683|15023|0|MBErrorDomain|209|2|0|0|0|0"
                parts = event.split('|')
                timestamp = datetime.fromisoformat(parts[0])

                item = {
                    'datetime': timestamp.isoformat(timespec='microseconds'),
                    'timestamp': timestamp.timestamp(),
                    'timestamp_desc': 'LastOnCondition error',
                    'saf_module': self.module_name,
                    'domain': parts[12],
                    'code': int(parts[13])
                    # TODO understand the meaning of the other fields
                }

                # FIXME below correlation is WRONG. The index of the BackupStateInfo error is not the same as the index of the LastOnConditionEvents
                try:
                    backupstateinfo = json_data['BackupStateInfo']['errors'][i]
                    item.update(backupstateinfo)
                except IndexError:
                    # could not find a correlating BackupStateInfo
                    pass
                item['message'] = f"MobileBackup: {item.get('localizedDescription', '')} in {item['domain']} ",
                result.append(item)

            # add PreflightSizing that does not have a timestamp
            for key, value in json_data.get('PreflightSizing', {}).items():
                timestamp = self.sysdiagnose_creation_datetime
                item = {
                    'type': 'MobileBackup PreflightSizing entry',
                    'datetime': timestamp.isoformat(timespec='microseconds'),
                    'timestamp': timestamp.timestamp(),
                    'timestamp_info': 'sysdiagnose creation',
                    'timestamp_desc': 'PreflightSizing entry',
                    'saf_module': self.module_name,
                    'key': key,
                    'size': value
                }
                try:
                    item['bundle_id'] = re.search(r'[^-]+Domain[^-]*-(.+)$', key).group(1)
                except Exception:
                    # not a bundle id
                    pass
                try:
                    item['domain'] = re.search(r'([^-]+Domain[^-]*)', key).group(1)
                except Exception:
                    # not a domain
                    pass
                item['message'] = f"{item['type']} bundle={item.get('bundle_id', '')} key={item['key']}"
                result.append(item)

        return result
