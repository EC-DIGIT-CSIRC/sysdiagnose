#! /usr/bin/env python3

# For Python3
# Script to print from Accessibility TCC logs
# Author: david@autopsit.org

from optparse import OptionParser
from utils import sqlite2json
import glob
import os
import sys
import misc

version_string = "sysdiagnose-Accessibility-TCC.py v2020-20-20 Version 1.0"

# ----- definition for parsing.py script -----#

parser_description = "Parsing Accessibility TCC logs"
parser_input = "Accessibility-TCC"
parser_call = "get_accessibility_tcc"

# --------------------------------------------#

# --------------------------------------------------------------------------- #


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


def get_accessibility_tcc(dbpath, ios_version=13):
    return parse_path(dbpath)


def print_accessibility_tcc(inputfile):
    sys.path.append(os.path.abspath('../'))
    print(sqlite2json.dump2json(get_accessibility_tcc(inputfile)))
    return


# --------------------------------------------------------------------------- #

def main():
    """
        Main function, to be called when used as CLI tool
    """

    print(f"Running {version_string}\n")

    usage = "\n%prog -i inputfile\n"

    parser = OptionParser(usage=usage)
    parser.add_option("-i", dest="inputfile",
                      action="store", type="string",
                      help="./logs/Accessibility/TCC.db to be parsed")
    (options, args) = parser.parse_args()

    # no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(-1)

    print_accessibility_tcc(options.inputfile)

# --------------------------------------------------------------------------- #


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()

# That's all folk ;)
