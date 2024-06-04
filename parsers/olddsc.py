#! /usr/bin/env python3

# For Python3
# Script to parse ./logs/olddsc files
# Author: david@autopsit.org
#
#
import glob
import os
import misc

parser_description = "Parsing olddsc files"


def get_log_files(log_root_path: str) -> dict:
    log_files_globs = [
        'logs/olddsc/*'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    return misc.load_plist_file_as_json(get_log_files(path)[0])
