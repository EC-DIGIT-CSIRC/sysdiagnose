#! /usr/bin/env python3

# For Python3
# Script to parse taskinfo.txt to ease parsing
# Author: david@autopsit.org
#
# TODO define output
# - search this artifact to extract more
#
import re
import glob
import os
from utils import tabbasedhierarchy


parser_description = "Parsing taskinfo txt file"


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'taskinfo.txt'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    processes = []

    with open(path, "r") as f:
        lines = f.readlines()

        result = re.search(r'(num tasks: )(\d+)', lines[0])
        if (result is not None):
            numb_tasks = int(result.group(2))
        else:
            numb_tasks = -1

        n = 1  # skip lines to right section
        extracted_block = []
        while n < len(lines):
            if 'thread ID:' in lines[n]:
                # end of main block OR thread block detected
                if 'threads:' in lines[n - 1]:
                    # end of main block detected
                    process = tabbasedhierarchy.parse_block(extracted_block)
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
                processes.append(process)
                extracted_block = []
                n = n + 1  # add one more to n as we are skipping the empty line
            else:
                extracted_block.append(lines[n])
            n = n + 1
    return {"numb_tasks": numb_tasks, "tasks": processes}
