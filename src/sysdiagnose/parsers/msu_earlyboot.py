#! /usr/bin/env python3

import glob
import os
import re
from datetime import UTC, datetime, timedelta

from sysdiagnose.utils.base import BaseParserInterface, Event, SysdiagnoseConfig, logger


class MSUEarlyBootTaskParser(BaseParserInterface):
    description = "Parsing MSUEarlyBootTask log files"
    format = "jsonl"  # by default json
    ios_version = ">=15.8"

    def __init__(self, config: SysdiagnoseConfig, case: dict) -> None:
        super().__init__(__file__, config, case)

    def get_log_files(self) -> list:
        log_files_globs = ["logs/MSU/MSUEarlyBootTask.log"]
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
            with open(log_file) as f:
                lines = f.readlines()

            timestamp = None
            timestamp_desc = "Timezone unknown. Ntp may also skew the time during boot."
            # extract initial timestamp from the first line
            for line in lines:
                if "update at time" in line:
                    m = re.search(r"update at time (.*)$", line)
                    timestamp_start = datetime.strptime(m.group(1), "%a %b %d %H:%M:%S %Y")
                    timestamp = timestamp_start.replace(tzinfo=UTC)  # ensure timezone is UTC
                    logger.info(f"Using timestamp from first line: {timestamp_start} (UTC)")
                    break
            # No timestamp found in the first line, no glory.
            if timestamp is None:
                timestamp = self.sysdiagnose_creation_datetime
                timestamp_start = self.sysdiagnose_creation_datetime
                timestamp_desc = "Date is from sysdiagnose creation, only time (HH:MM:SS) is from the log."
                logger.warning(timestamp_desc)

            previous_timestamp = None
            for line in lines:
                if line.strip() == "":
                    continue

                if line[8] == ":":
                    time_str, message = line.split(": ", 1)
                    # change the time of the timestamp_start and store it in new variable
                    timestamp = timestamp_start.replace(
                        hour=int(time_str[:2]), minute=int(time_str[3:5]), second=int(time_str[6:8])
                    )

                    # detect day rollover (time went backwards = midnight crossed)
                    if previous_timestamp is not None and timestamp < previous_timestamp:
                        timestamp_start += timedelta(days=1)
                        timestamp = timestamp_start.replace(
                            hour=int(time_str[:2]), minute=int(time_str[3:5]), second=int(time_str[6:8])
                        )

                    previous_timestamp = timestamp
                    entry = Event(
                        datetime=timestamp,
                        message=message.strip(),
                        module=self.module_name,
                        timestamp_desc=timestamp_desc,
                        data={},
                    )
                    result.append(entry.to_dict())
                else:  # continuation of previous line
                    result[-1]["message"] += "\n" + line.strip()

        return result
