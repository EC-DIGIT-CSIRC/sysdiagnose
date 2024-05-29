#! /usr/bin/env python3

# For Python3
# Script to print from iTunes Store
# Author: david@autopsit.org

from optparse import OptionParser
from utils import sqlite2json
import glob
import json
import os
import sys
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
    return misc.json_serializable(sqlite2json.sqlite2struct(path))


def get_itunesstore(dbpath, ios_version=13):
    itunes = sqlite2json.sqlite2struct(dbpath)
    return json.loads(sqlite2json.dump2json(itunes))


def print_itunesstore(inputfile):
    print(get_itunesstore(inputfile))
    return


# --------------------------------------------------------------------------- #

def main():
    """
        Main function, to be called when used as CLI tool
    """
    sys.path.append(os.path.abspath('../'))

    print(f"Running {version_string}\n")

    usage = "\n%prog -i inputfile\n"

    parser = OptionParser(usage=usage)
    parser.add_option("-i", dest="inputfile",
                      action="store", type="string",
                      help="./logs/itunesstored/downloads.*.sqlitedb to be parsed")
    (options, args) = parser.parse_args()

    # no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(-1)

    print_itunesstore(options.inputfile)

# --------------------------------------------------------------------------- #


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()

# That's all folk ;)
