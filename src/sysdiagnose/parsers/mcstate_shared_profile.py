#! /usr/bin/env python3

import glob
import os
from datetime import UTC, datetime

from sysdiagnose.utils import misc
from sysdiagnose.utils.base import BaseParserInterface, Event, SysdiagnoseConfig


class McStateSharedProfileParser(BaseParserInterface):
    description = "Parsing MCState Shared Profile stub files"
    format = "jsonl"  # by default json

    def __init__(self, config: SysdiagnoseConfig, case: dict) -> None:
        super().__init__(__file__, config, case)

    def is_compatible(self) -> bool:
        version_compatibility = super().is_compatible()
        # not compatible with Apple TV
        device_compatibility = "AppleTV" not in self.case_model
        # both need to be compatible
        return version_compatibility and device_compatibility

    def get_log_files(self) -> list:
        log_files_globs = ["logs/MCState/Shared/profile-*.stub"]
        log_files = []
        for log_files_glob in log_files_globs:
            for item in glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)):
                if os.path.getsize(item) > 0:
                    log_files.append(item)
        return log_files

    def execute(self) -> list | dict:
        """
        this is the function that will be called
        """
        result = []
        log_files = self.get_log_files()
        for log_file in log_files:
            entry = misc.load_plist_file_as_json(log_file)
            timestamp = datetime.strptime(entry["InstallDate"], "%Y-%m-%dT%H:%M:%S.%f")
            timestamp = timestamp.replace(tzinfo=UTC)  # ensure timezone is UTC
            event = Event(
                datetime=timestamp,
                message="# ".join(
                    [
                        entry.get("PayloadDescription", ""),
                        entry.get("PayloadDisplayName", ""),
                        entry.get("PayloadOrganization", ""),
                    ]
                ),
                module=self.module_name,
                timestamp_desc=f"MCState {entry['PayloadType']}",
                data=entry,
            )
            result.append(event.to_dict())

        return result
