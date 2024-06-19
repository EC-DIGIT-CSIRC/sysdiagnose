#! /usr/bin/env python3

# For Python3
# Script to print the values from logs/tailspindb/UUIDToBinaryLocations (XML plist)
# Uses Python3's plistlib
# Author: cheeky4n6monkey@gmail.com
#
# Change log: David DURVAUX - add function are more granular approach

import os
import glob
import utils.misc as misc

parser_description = "Parsing UUIDToBinaryLocations plist file"


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'logs/tailspindb/UUIDToBinaryLocations'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    try:
        fname = get_log_files(path)[0]
        return misc.load_plist_file_as_json(fname)
    except IndexError:
        return {'error': 'No UUIDToBinaryLocations file present'}


def printResult(data):
    """
        Print the hashtable produced by getUUID2Path to console as UUID, path
    """
    if data:
        for uuid in data.keys():
            print(f"{str(uuid)}, {str(data[uuid])}")
    print(f"\n {str(len(data.keys()))} GUIDs found\n")
    return
