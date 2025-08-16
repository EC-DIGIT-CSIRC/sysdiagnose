#! /usr/bin/env python3

import glob
import os
from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, Event
from sysdiagnose.utils import misc
from datetime import datetime, timezone
import re


class MobileBackupParser(BaseParserInterface):
    description = "Parsing mobilebackup plist file"
    format = 'jsonl'

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
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
            # for i, event in enumerate(json_data.get('LastOnConditionEvents', [])):
            #     # "2023-02-22T10:24:49.051-08:00|158966.533|1|1|0|1|1|0|120|73683|15023|0|MBErrorDomain|209|2|0|0|0|0"
            #     parts = event.split('|')
            #     timestamp = datetime.fromisoformat(parts[0])

            #     item = {

            #     }

            #     # FIXME below correlation is WRONG. The index of the BackupStateInfo error is not the same as the index of the LastOnConditionEvents
            #     try:
            #         backupstateinfo = json_data['BackupStateInfo']['errors'][i]
            #         item.update(backupstateinfo)
            #     except IndexError:
            #         # could not find a correlating BackupStateInfo
            #         pass

            #     event = Event(
            #         datetime=timestamp,
            #         message=f"MobileBackup: {item.get('localizedDescription', '')} in {item['domain']} ",
            #         module=self.module_name,
            #         timestamp_desc='LastOnCondition error',
            #         data={
            #             'domain': parts[12],
            #             'code': int(parts[13])
            #             # TODO understand the meaning of the other fields
            #         }
            #     )
            #     result.append(event.to_dict())

            # add BackupStateInfo errors
            for item in json_data.get('BackupStateInfo', {}).get('errors', []):
                try:
                    timestamp = datetime.strptime(item['date'], '%Y-%m-%dT%H:%M:%S.%f')
                    timestamp = timestamp.replace(tzinfo=timezone.utc)  # ensure timezone is UTC
                except Exception:
                    continue

                event = Event(
                    datetime=timestamp,
                    message=f"MobileBackup: {item.get('localizedDescription', '')} in {item['domain']} ",
                    module=self.module_name,
                    timestamp_desc='BackupStateInfo error',
                    data=item
                )
                event.data.pop('date')

                result.append(event.to_dict())

            # add PreflightSizing that does not have a timestamp
            for key, value in json_data.get('PreflightSizing', {}).items():
                timestamp = self.sysdiagnose_creation_datetime
                item = {
                    'type': 'MobileBackup PreflightSizing entry',
                    'timestamp_info': 'sysdiagnose creation',
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

                event = Event(
                    datetime=timestamp,
                    message=f"{item['type']} bundle={item.get('bundle_id', '')} key={item['key']}",
                    module=self.module_name,
                    timestamp_desc='PreflightSizing entry',
                    data=item
                )
                result.append(event.to_dict())

        return result
