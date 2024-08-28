#! /usr/bin/env python3

# For Python3
# Script to parse ps.txt to ease parsing
# Author: david@autopsit.org
#
# TODO define output
# - json
# - tree structure
# - simplified
#
import glob
import os
import re
from utils.base import BaseParserInterface


class PsThreadParser(BaseParserInterface):
    description = "Parsing ps_thread.txt file"

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

    def execute(self) -> list | dict:
        result = []
        try:
            with open(self.get_log_files()[0], "r") as f:
                header = re.split(r"\s+", f.readline().strip())
                header_length = len(header)
                row = None
                for line in f:
                    if '??' in line:
                        # append previous entry
                        if row:
                            result.append(row)

                        patterns = line.strip().split(None, header_length - 1)
                        row = {'THREADS': 1}
                        # merge last entries together, as last entry may contain spaces
                        for col in range(header_length):
                            # try to cast as int, float and fallback to string
                            col_name = header[col]
                            try:
                                row[col_name] = int(patterns[col])
                                continue
                            except ValueError:
                                try:
                                    row[col_name] = float(patterns[col])
                                except ValueError:
                                    row[col_name] = patterns[col]
                    else:
                        row['THREADS'] += 1
                # append last entry
                if row:
                    result.append(row)
                return result
        except IndexError:
            return {'error': 'No ps_thread.txt file present'}
