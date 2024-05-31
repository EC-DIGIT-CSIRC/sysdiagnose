#! /usr/bin/env python3

# For Python3
# Script to parse the swcutil_show.txt file
# Author: Emilien Le Jamtel

import json
import glob
import misc
import os

parser_description = "Parsing com.apple.wifi plist files"


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'WiFi/*.plist',
        'WiFi/com.apple.wifi.recent-networks.json'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    if path.endswith('.json'):
        with open(path, 'r') as f:
            return json.load(f)
    if path.endswith('.plist'):
        return misc.load_plist_file_as_json(path)
