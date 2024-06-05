#! /usr/bin/env python3

# For Python3
# Script to extract the values from logs/Networking/com.apple.networkextension.plist
# Author: Emilien Le Jamtel


import utils.misc as misc
import os
import glob


parser_description = "Parsing networkextension plist file"


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'logs/Networking/com.apple.networkextension.plist'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    try:
        return misc.load_plist_file_as_json(get_log_files(path)[0])
    except IndexError:
        return {'error': 'No com.apple.networkextension.plist file present'}
