#! /usr/bin/env python3

# For Python3
# Script to print from Accessibility TCC logs
# Author: david@autopsit.org

from utils import sqlite2json
import glob
import os
import utils.misc as misc
import json

version_string = "sysdiagnose-Accessibility-TCC.py v2020-20-20 Version 1.0"

# ----- definition for parsing.py script -----#

parser_description = "Parsing Accessibility TCC logs"


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'logs/Accessibility/TCC.db'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    # only one file to parse
    try:
        return misc.json_serializable(sqlite2json.sqlite2struct(get_log_files(path)[0]))
    except IndexError:
        return {'error': 'No TCC.db file found in logs/Accessibility/ directory'}


def parse_path_to_folder(path: str, output_folder: str) -> bool:
    result = parse_path(path)
    output_file = os.path.join(output_folder, f"{__name__.split('.')[-1]}.json")
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=4)
