#! /usr/bin/env python3

# For Python3
# Script to print from Accessibility TCC logs
# Author: david@autopsit.org

from utils import sqlite2json
import glob
import os
import misc

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
    return misc.json_serializable(sqlite2json.sqlite2struct(path))
