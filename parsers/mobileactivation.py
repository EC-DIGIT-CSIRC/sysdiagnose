#! /usr/bin/env python3

# For Python3
# Script to parse the swcutil_show.txt file
# Author: Emilien Le Jamtel

import glob
import os
from utils import multilinelog
import json

parser_description = "Parsing mobileactivation logs file"


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'logs/MobileActivation/mobileactivationd.log*'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    result = []
    for logfile in get_log_files(path):
        result.extend(multilinelog.extract_from_file(logfile))
    return result


def parse_path_to_folder(path: str, output_folder: str) -> bool:
    result = parse_path(path)
    output_file = os.path.join(output_folder, f"{__name__.split('.')[-1]}.json")
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=4)
