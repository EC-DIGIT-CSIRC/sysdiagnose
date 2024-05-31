#! /usr/bin/env python3

# For Python3
# Script to print the values from logs/tailspindb/UUIDToBinaryLocations (XML plist)
# Uses Python3's plistlib
# Author: cheeky4n6monkey@gmail.com
#
# Change log: David DURVAUX - add function are more granular approach

import os
import glob
import misc

version_string = "sysdiagnose-uuid2path.py v2020-02-07 Version 2.0"

# ----- definition for parsing.py script -----#
# -----         DO NOT DELETE             ----#

parser_description = "Parsing UUIDToBinaryLocations plist file"
parser_input = "UUIDToBinaryLocations"
parser_call = "getUUID2path"

# --------------------------------------------#

# --------------------------------------------------------------------------- #


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'logs/tailspindb/UUIDToBinaryLocations'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    return misc.load_plist_file_as_json(path)


def printResult(data):
    """
        Print the hashtable produced by getUUID2Path to console as UUID, path
    """
    if data:
        for uuid in data.keys():
            print(f"{str(uuid)}, {str(data[uuid])}")
    print(f"\n {str(len(data.keys()))} GUIDs found\n")
    return
