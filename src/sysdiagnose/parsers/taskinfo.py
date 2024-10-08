#! /usr/bin/env python3

# For Python3
# Script to parse taskinfo.txt to ease parsing
# Author: david@autopsit.org
#

import re
import glob
import os
from sysdiagnose.utils import tabbasedhierarchy
from sysdiagnose.utils.base import BaseParserInterface
from datetime import timedelta


class TaskinfoParser(BaseParserInterface):
    description = "Parsing taskinfo txt file"
    format = 'jsonl'

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'taskinfo.txt'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list:
        path = self.get_log_files()[0]
        events = []
        try:
            with open(path, "r") as f:
                lines = f.readlines()

                result = re.search(r'(num tasks: )(\d+)', lines[0])
                if (result is not None):
                    numb_tasks = int(result.group(2))
                    events.append({
                        'timestamp': self.sysdiagnose_creation_datetime.timestamp(),
                        'datetime': self.sysdiagnose_creation_datetime.isoformat(timespec='microseconds'),
                        'tasks': numb_tasks,
                        'datetime_description': f"{numb_tasks} tasks/programs running at sysdiagnose creation time.",
                    })

                n = 1  # skip lines to right section
                extracted_block = []
                while n < len(lines):
                    if 'thread ID:' in lines[n]:
                        # end of main block OR thread block detected
                        if 'threads:' in lines[n - 1]:
                            # end of main block detected
                            process = tabbasedhierarchy.parse_block(extracted_block)
                            # extract process id and process_name from process['process'] line
                            process['pid'] = int(re.search(r'\[(\d+)\]', process['process']).group(1))
                            process['name'] = re.search(r'"([^"]+)"', process['process']).group(1)
                            process['threads'] = []
                            pass
                        else:
                            # start of thread_block detected
                            # this is also the end of the previous thread block
                            process['threads'].append(tabbasedhierarchy.parse_block(extracted_block))
                            pass
                        # be ready to accept new thread block
                        extracted_block = []
                        extracted_block.append(lines[n])
                    if n >= 41058:
                        pass
                    if lines[n].strip() == "" and lines[n + 1].strip() == "":
                        # start of new process block detected
                        # this is also the end of the previous thread block
                        process['threads'].append(tabbasedhierarchy.parse_block(extracted_block))
                        # compute start time: start time = sysdiagnose_creation_time minus process['run time']
                        seconds = int(process['run time'].split()[0])
                        timestamp = self.sysdiagnose_creation_datetime - timedelta(seconds=seconds)
                        process['timestamp'] = timestamp.timestamp()
                        process['datetime'] = timestamp.isoformat(timespec='microseconds')
                        process['datetime_description'] = "Process launched at the timestamp, calculated from sysdiagnose creation time minus process run time"
                        events.append(process)
                        extracted_block = []
                        n = n + 1  # add one more to n as we are skipping the empty line
                    else:
                        extracted_block.append(lines[n])
                    n = n + 1
            return events
        except IndexError:
            return []
