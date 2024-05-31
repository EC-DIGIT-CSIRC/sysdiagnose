#! /usr/bin/env python3

# For Python3
# Sysdiagnose Shutdown logs
# Author: Benoit Roussile

import datetime
import glob
import os
import re

parser_description = "Parsing shutdown.log file"

CLIENTS_ARE_STILL_HERE_LINE = "these clients are still here"
REMAINING_CLIENT_PID_LINE = "remaining client pid"
SIGTERM_LINE = "SIGTERM"


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'system_logs.logarchive/Extra/shutdown.log'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    # read log file content
    log_lines = ""
    with open(path, "r") as f:
        log_lines = f.readlines()

    json_object = {}
    parsed_data = {}
    index = 0
    # go through log file
    while index < len(log_lines):
        # look for begining of shutdown sequence
        if CLIENTS_ARE_STILL_HERE_LINE in log_lines[index]:
            running_processes = []
            while not (SIGTERM_LINE in log_lines[index]):
                if (REMAINING_CLIENT_PID_LINE in log_lines[index]):
                    result = re.search(r".*: (\b\d+) \((.*)\).*", log_lines[index])
                    pid = result.groups()[0]
                    binary_path = result.groups()[1]
                    process = pid + ":" + binary_path
                    if not (process in running_processes):
                        running_processes.append(process)
                index += 1
            # compute timestamp from SIGTERM line
            result = re.search(r".*\[(\d+)\].*", log_lines[index])
            timestamp = result.groups()[0]
            time = str(datetime.datetime.fromtimestamp(int(timestamp), datetime.UTC))
            # add entries
            parsed_data[time] = []
            for p in running_processes:
                parsed_data[time].append({"pid": p.split(":")[0], "path": p.split(":")[1]})
        index += 1

    json_object["data"] = parsed_data

    return json_object
