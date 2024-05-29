#! /usr/bin/env python3

# For Python3
# Script to print from powerlogs (last 3 days of logs)
# Author: david@autopsit.org

from optparse import OptionParser
from utils import sqlite2json
import glob
import os
import sys


version_string = "sysdiagnose-powerlogs.py v2020-20-19 Version 1.0"

# ----- definition for parsing.py script -----#
# -----         DO NOT DELETE             ----#

parser_description = "Parsing  powerlogs database"
parser_input = "powerlogs"
parser_call = "get_powerlogs"

# --------------------------------------------#

# --------------------------------------------------------------------------- #


def get_log_files(log_root_path: str) -> list:
    """
        Get the list of log files to be parsed
    """
    log_files_globs = [
        'logs/powerlogs/powerlog_*',
        # 'logs/powerlogs/log_*'  # LATER is this file of interest?
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    return sqlite2json.sqlite2struct(path)


def get_powerlogs(dbpath, ios_version=13):

    powerlogs = sqlite2json.sqlite2struct(dbpath)
    return powerlogs


def print_powerlogs(inputfile):
    print(get_powerlogs(inputfile))
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
                      help="./logs/powerlogs/powerlog_2019-11-07_17-23_ED7F7E2B.PLSQL to be parsed")
    (options, args) = parser.parse_args()

    # no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(-1)
    # print(options.inputfile)
    print_powerlogs(options.inputfile)

# --------------------------------------------------------------------------- #


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()

# That's all folk ;)
