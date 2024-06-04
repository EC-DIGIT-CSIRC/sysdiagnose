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


def parse_file(fname: str) -> dict | list:
    if fname.endswith('.json'):
        with open(fname, 'r') as f:
            return json.load(f)
    if fname.endswith('.plist'):
        return misc.load_plist_file_as_json(fname)


def parse_path(path: str) -> dict:
    result = {}
    for logfile in get_log_files(path):
        end_of_path = logfile[len(path):].lstrip(os.path.sep)  # take the path after the root path
        result[end_of_path] = parse_file(logfile)
    return result


def parse_path_to_folder(path: str, output: str) -> bool:
    os.makedirs(output, exist_ok=True)
    for logfile in get_log_files(path):
        try:
            json_data = parse_file(logfile)
        except Exception as e:
            json_data = {"error": str(e)}
        end_of_path = logfile[len(path):].lstrip(os.path.sep)   # take the path after the root path
        output_filename = end_of_path.replace(os.path.sep, '_') + '.json'  # replace / with _ in the path
        with open(os.path.join(output, output_filename), 'w') as f:
            f.write(json_data)
