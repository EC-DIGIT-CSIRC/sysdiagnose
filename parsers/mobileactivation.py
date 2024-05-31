#! /usr/bin/env python3

# For Python3
# Script to parse the swcutil_show.txt file
# Author: Emilien Le Jamtel

import glob
import os
from utils import multilinelog

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
    return multilinelog.extract_from_file(path)
