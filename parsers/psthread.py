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


parser_description = "Parsing ps_thread.txt file"


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'ps_thread.txt'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    with open(path, "r") as fd:
        input = fd.readlines()
        input_clean = []
        for line in input:
            if "??" in line:
                input_clean.append(line)
        headers = [h for h in ' '.join(input[0].strip().split()).split() if h]
        raw_data = map(lambda s: s.strip().split(None, len(headers) - 1), input_clean)
        return [dict(zip(headers, r)) for r in raw_data]
