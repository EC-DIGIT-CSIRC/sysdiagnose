#! /usr/bin/env python3

# For Python3
# Sysdiagnose Shutdown logs
# Author: Benoit Roussile

import datetime
import glob
import os
import re
from utils.base import BaseParserInterface

CLIENTS_ARE_STILL_HERE_LINE = "these clients are still here"
REMAINING_CLIENT_PID_LINE = "remaining client pid"
SIGTERM_LINE = "SIGTERM"


class ShutdownLogsParser(BaseParserInterface):
    description = 'Parsing shutdown.log file'
    format = 'jsonl'

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'system_logs.logarchive/Extra/shutdown.log'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list:
        return ShutdownLogsParser.parse_file(self.get_log_files()[0])

    def parse_file(path: str) -> list:
        # read log file content
        log_lines = ""
        try:
            with open(path, "r") as f:
                log_lines = f.readlines()
        except IndexError:
            return {'error': 'No shutdown.log file present in system_logs.logarchive/Extra/ directory'}

        events = []
        index = 0
        # go through log file
        while index < len(log_lines):
            # look for begining of shutdown sequence
            if CLIENTS_ARE_STILL_HERE_LINE in log_lines[index]:
                running_processes = {}
                time_waiting = 0
                while not (SIGTERM_LINE in log_lines[index]):
                    if CLIENTS_ARE_STILL_HERE_LINE in log_lines[index]:
                        time_waiting = re.search(r'After ([\d\.]+)s,', log_lines[index]).group(1)
                    if (REMAINING_CLIENT_PID_LINE in log_lines[index]):
                        result = re.search(r".*: (\b\d+) \((.*)\).*", log_lines[index])
                        pid = result.groups()[0]
                        binary_path = result.groups()[1]
                        running_processes[pid] = {
                            "pid": int(pid),
                            "path": binary_path,
                            "command": '/'.join(binary_path.split('/')[:-1]),
                            "time_waiting": float(time_waiting)
                        }
                    index += 1
                # compute timestamp from SIGTERM line
                result = re.search(r".*\[(\d+)\].*", log_lines[index])
                timestamp = datetime.datetime.fromtimestamp(int(result.groups()[0]), datetime.UTC)

                # add entries
                for item in running_processes.values():
                    item['timestamp'] = timestamp.timestamp()
                    item['datetime'] = timestamp.isoformat()
                    item['event'] = f"{item['command']} is still there during shutdown after {item['time_waiting']}s"
                    events.append(item)
            index += 1

        return events
