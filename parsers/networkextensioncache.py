#! /usr/bin/env python3

# For Python3
# Script to extract the values from logs/Networking/com.apple.networkextension.plist
# Author: Emilien Le Jamtel


import glob
import os
import misc


parser_description = "Parsing networkextensioncache plist file"


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'logs/Networking/com.apple.networkextension.cache.plist'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    return misc.load_plist_file_as_json(get_log_files(path)[0])
