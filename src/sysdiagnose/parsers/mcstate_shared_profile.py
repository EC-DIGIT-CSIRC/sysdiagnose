#! /usr/bin/env python3

import glob
import os
from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, Event
import sysdiagnose.utils.misc as misc
from datetime import datetime, timezone


class McStateSharedProfileParser(BaseParserInterface):
    description = "Parsing MCState Shared Profile stub files"
    format = "jsonl"  # by default json

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            "logs/MCState/Shared/profile-*.stub"
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            for item in glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)):
                if os.path.getsize(item) > 0:
                    log_files.append(item)
        return log_files

    def execute(self) -> list | dict:
        '''
        this is the function that will be called
        '''
        result = []
        log_files = self.get_log_files()
        for log_file in log_files:
            entry = misc.load_plist_file_as_json(log_file)
            timestamp = datetime.strptime(entry['InstallDate'], '%Y-%m-%dT%H:%M:%S.%f')
            timestamp = timestamp.replace(tzinfo=timezone.utc)  # ensure timezone is UTC

            # Extract the SHA-256 hash from the stub filename (profile-{hash}.stub)
            stub_filename = os.path.basename(log_file)
            if stub_filename.startswith('profile-') and stub_filename.endswith('.stub'):
                entry['ProfileStubHash'] = stub_filename[len('profile-'):-len('.stub')]

            event = Event(
                datetime=timestamp,
                message='# '.join([entry.get('PayloadDescription', ''), entry.get('PayloadDisplayName', ''), entry.get('PayloadOrganization', '')]),
                module=self.module_name,
                timestamp_desc=f"MCState {entry['PayloadType']}",
                data=entry
            )
            result.append(event.to_dict())

        return result
