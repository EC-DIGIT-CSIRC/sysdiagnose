#! /usr/bin/env python3

# For Python3
# Script to print from iTunes Store
# Author: david@autopsit.org

from utils import sqlite2json
import glob
import os
import misc

version_string = "sysdiagnose-itunesstore.py v2020-20-19 Version 1.0"

# ----- definition for parsing.py script -----#
# -----         DO NOT DELETE             ----#

parser_description = "Parsing iTunes store logs"
parser_input = "itunesstore"
parser_call = "get_itunesstore"

# --------------------------------------------#

# --------------------------------------------------------------------------- #


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'logs/itunesstored/downloads.*.sqlitedb'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    # there's only one file to parse
    return misc.json_serializable(sqlite2json.sqlite2struct(get_log_files(path)[0]))
