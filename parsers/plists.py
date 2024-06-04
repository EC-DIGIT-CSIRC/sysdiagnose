#! /usr/bin/env python3

import glob
import misc
import os
import json

parser_description = "Parsing any pslist into json"


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        '**/*.plist'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob), recursive=True))

    return log_files


def parse_path(path: str) -> dict:
    result = {}
    for logfile in get_log_files(path):
        try:
            json_data = misc.load_plist_file_as_json(logfile)
        except Exception as e:
            json_data = {"error": str(e)}
        end_of_path = logfile[len(path):].lstrip(os.path.sep)  # take the path after the root path
        result[end_of_path] = json_data
    return result


def parse_path_to_folder(path: str, output: str) -> bool:
    os.makedirs(output, exist_ok=True)
    for logfile in get_log_files(path):
        try:
            json_data = misc.load_plist_file_as_json(logfile)
        except Exception as e:
            json_data = {"error": str(e)}
        end_of_path = logfile[len(path):].lstrip(os.path.sep)   # take the path after the root path
        output_filename = end_of_path.replace(os.path.sep, '_') + '.json'  # replace / with _ in the path
        with open(os.path.join(output, output_filename), 'w') as f:
            json.dump(json_data, f, indent=4)
