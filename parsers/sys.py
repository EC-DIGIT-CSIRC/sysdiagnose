#! /usr/bin/env python3

# For Python3
# Script to print the values from /logs/SystemVersion/SystemVersion.plist
# Author: cheeky4n6monkey@gmail.com
#
# Change log: David DURVAUX - add function are more granular approach

import sys
from optparse import OptionParser
import plistlib
import os
import glob

version_string = "sysdiagnose-sys.py v2019-05-10 Version 2.0"

# ----- definition for parsing.py script -----#
# -----         DO NOT DELETE             ----#

parser_description = "Parsing SystemVersion plist file"
parser_input = "systemversion"
parser_call = "getProductInfo"

# --------------------------------------------#


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'logs/SystemVersion/SystemVersion.plist'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    return getProductInfo(path)


# --------------------------------------------------------------------------- #
# XXX FIXME: this is obviously a very generic function and could be generalized and moved to misc/

def getProductInfo(path="./logs/SystemVersion/SystemVersion.plist", ios_version=13):
    """
        return an hash table with  the following structure
        {
            "ProductName" : "",
            "ProductionVersion" : "",
            "ProductBuildVersion" : ""
        }
        Non populated fields are filled with a None value
    """
    result = {
        "ProductName": None,
        "ProductionVersion": None,
        "ProductBuildVersion": None
    }
    try:
        with open(path, 'rb') as fd:
            plist = plistlib.load(fd)
        for key in ["ProductName", "ProductVersion", "ProductBuildVersion", "BuildID", "SystemImageID"]:
            if key in plist.keys():
                result[key] = plist[key]
            else:
                print(f"WARNING: {key} not found in plist file {path}. Ignoring key.", file=sys.stderr)
    except Exception as e:
        print(f"Could not parse {path}. Reason: {str(e)}", file=sys.stderr)
    return result


def main():
    """
        Main function, to be called when used as CLI tool
    """
    if sys.version_info[0] < 3:
        print("Must be using Python 3! Exiting ...", file=sys.stderr)
        sys.exit(-1)

    print(f"Running {version_string}\n")

    usage = "\n%prog -i inputfile\n"

    parser = OptionParser(usage=usage)
    parser.add_option("-i", dest="inputfile", action="store", type="string",
                      help="/logs/SystemVersion/SystemVersion.plist To Be Searched")
    (options, args) = parser.parse_args()

    if options.inputfile:
        pl = getProductInfo(options.inputfile)
        print(f"ProductName = {pl['ProductName']}")       # XXX #9 FIXME: should that return the structure instead of print() ing it?
        print(f"ProductVersion = {pl['ProductVersion']}")
        print(f"ProductBuildVersion = {pl['ProductBuildVersion']}")
    else:
        print("WARNING -i option is mandatory!", file=sys.stderr)


# --------------------------------------------------------------------------- #

"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()


# That's all folk ;)
