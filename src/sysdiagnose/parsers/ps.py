#! /usr/bin/env python3

# For Python3
# Script to parse ps.txt to ease parsing
# Author: david@autopsit.org
#

from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, logger, Event
from sysdiagnose.utils.misc import snake_case
import glob
import os
import re


class PsParser(BaseParserInterface):
    description = "Parsing ps.txt file"
    format = "jsonl"

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'ps.txt'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        for log_file in self.get_log_files():
            return self.parse_file(log_file)
        return {'error': ['No ps.txt file present']}

    def parse_file(self, filename):
        result = []
        try:
            with open(filename, "r") as f:
                header = re.split(r"\s+", f.readline().strip())
                header_length = len(header)

                # print(f"Found header: {header}")
                for line in f:
                    patterns = line.strip().split(None, header_length - 1)
                    entry = {}
                    # merge last entries together, as last entry may contain spaces
                    for col in range(header_length):
                        # try to cast as int, float and fallback to string
                        col_name = snake_case(header[col])
                        try:
                            entry[col_name] = int(patterns[col])
                            continue
                        except ValueError:
                            try:
                                entry[col_name] = float(patterns[col])
                            except ValueError:
                                entry[col_name] = patterns[col]
                    timestamp = self.sysdiagnose_creation_datetime
                    event = Event(
                        datetime=timestamp,
                        message=f"Process {entry['command']} [{entry['pid']}] running as {entry['user']}",
                        module=self.module_name,
                        timestamp_desc='process running',
                        data=entry
                    )
                    event.data['timestamp_info'] = 'sysdiagnose creation time'
                    result.append(event.to_dict())
                return result
        except Exception:
            logger.exception("Could not parse ps.txt")
            return []

    def exclude_known_goods(processes: dict, known_good: dict) -> list[dict]:
        """
        Exclude known good processes from the given list of processes.

        Args:
            processes (dict): The output from parse_file() to check.
            known_good (dict): The output of parse_file() from a known good.

        Returns:
            dict: The updated list of processes with known good processes excluded.
        """

        known_good_cmd = [x['command'] for x in known_good]

        for proc in processes:
            if proc['command'] in known_good_cmd:
                processes.remove(proc)

        return processes
