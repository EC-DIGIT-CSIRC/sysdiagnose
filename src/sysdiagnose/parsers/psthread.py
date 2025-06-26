#! /usr/bin/env python3

# For Python3
# Script to parse ps.txt to ease parsing
# Author: david@autopsit.org
#

import glob
import os
import re
from sysdiagnose.utils.base import BaseParserInterface, logger, Event
from sysdiagnose.utils.misc import snake_case


class PsThreadParser(BaseParserInterface):
    description = "Parsing ps_thread.txt file"
    format = 'jsonl'

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'ps_thread.txt'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list:
        # not really easy to conver to true timebased jsonl, as the timestamp is complex to compute.
        # so we just fall back to the sysdiagnose creation timestamp
        timestamp = self.sysdiagnose_creation_datetime

        result = []
        try:
            with open(self.get_log_files()[0], "r") as f:
                header = re.split(r"\s+", f.readline().strip())
                header_length = len(header)
                event = None
                for line in f:
                    if '??' in line:
                        # append previous entry
                        if event:
                            event.message = f"{event.data['command']} [{event.data['pid']}] as {event.data['user']}"
                            result.append(event.to_dict())

                        patterns = line.strip().split(None, header_length - 1)
                        event = Event(
                            datetime=timestamp,
                            message='',
                            module=self.module_name,
                            timestamp_desc='running process',
                            data={
                                'timestamp_info': 'sysdiagnose creation time',
                                'threads': 1}
                        )
                        # merge last entries together, as last entry may contain spaces
                        for col in range(header_length):
                            # try to cast as int, float and fallback to string
                            col_name = snake_case(header[col])
                            try:
                                event.data[col_name] = int(patterns[col])
                                continue
                            except ValueError:
                                try:
                                    event.data[col_name] = float(patterns[col])
                                except ValueError:
                                    event.data[col_name] = patterns[col]
                    else:
                        event.data['threads'] += 1
                # append last entry
                if event:
                    event.message = f"{event.data['command']} [{event.data['pid']}] as {event.data['user']}"
                    result.append(event.to_dict())
                return result
        except IndexError:
            logger.warning('No ps_thread.txt file present')
            return []
