#! /usr/bin/env python3

# For Python3
# Script to print from powerlogs (last 3 days of logs)
# Author: david@autopsit.org

from utils import sqlite2json
import glob
import os
from utils.misc import merge_dicts
import json


parser_description = "Parsing  powerlogs database"


def get_log_files(log_root_path: str) -> list:
    """
        Get the list of log files to be parsed
    """
    log_files_globs = [
        'logs/powerlogs/powerlog_*',
        'logs/powerlogs/log_*'  # LATER is this file of interest?
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> dict:
    result = {}
    for logfile in get_log_files(path):
        db_json = sqlite2json.sqlite2struct(logfile)
        result = merge_dicts(result, db_json)  # merge both
    return result


def parse_path_to_folder(path: str, output_folder: str) -> bool:
    result = parse_path(path)
    output_file = os.path.join(output_folder, f"{__name__.split('.')[-1]}.json")
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=4)
