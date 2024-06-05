#! /usr/bin/env python3

# For Python3
# Script to print the values from /logs/SystemVersion/SystemVersion.plist
# Author: cheeky4n6monkey@gmail.com
#
# Change log: David DURVAUX - add function are more granular approach

import os
import glob
import utils.misc as misc

parser_description = "Parsing SystemVersion plist file"


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'logs/SystemVersion/SystemVersion.plist'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    try:
        return misc.load_plist_file_as_json(get_log_files(path)[0])
    except IndexError:
        return {'error': 'No SystemVersion.plist file present'}


'''
old code to print the values
    if options.inputfile:
        pl = getProductInfo(options.inputfile)
        print(f"ProductName = {pl['ProductName']}")       # XXX #9 FIXME: should that return the structure instead of print() ing it?
        print(f"ProductVersion = {pl['ProductVersion']}")
        print(f"ProductBuildVersion = {pl['ProductBuildVersion']}")
    else:
        print("WARNING -i option is mandatory!", file=sys.stderr)
'''
