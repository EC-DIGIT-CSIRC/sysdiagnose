#! /usr/bin/env python3

# For Python3
# Script to print from powerlogs (last 3 days of logs)
# Author: david@autopsit.org

import os
import sys
from optparse import OptionParser

version_string = "sysdiagnose-powerlogs.py v2020-20-19 Version 1.0"

# ----- definition for parsing.py script -----#
# -----         DO NET DELETE             ----#

parser_description = "Parsing  powerlogs database"
parser_input = "powerlogs"
parser_call = "get_powerlogs"

# --------------------------------------------#

# --------------------------------------------------------------------------- #


def get_powerlogs(dbpath, ios_version=13):
    sys.path.append(os.path.abspath('../'))
    from utils import times
    from utils import sqlite2json

    powerlogs = sqlite2json.sqlite2struct(dbpath)
    return sqlite2json.dump2json(powerlogs)


def print_powerlogs(inputfile):
    print(get_powerlogs(inputfile))
    return


# --------------------------------------------------------------------------- #

def main():
    """
        Main function, to be called when used as CLI tool
    """
    if sys.version_info[0] < 3:
        print("Must be using Python 3! Exiting ...")
        exit(-1)

    print("Running " + version_string + "\n")

    usage = "\n%prog -i inputfile\n"

    parser = OptionParser(usage=usage)
    parser.add_option("-i", dest="inputfile",
                      action="store", type="string",
                      help="./logs/powerlogs/powerlog_2019-11-07_17-23_ED7F7E2B.PLSQL to be parsed")
    (options, args) = parser.parse_args()

    # no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        exit(-1)
    print(options.inputfile)
    print_powerlogs(options.inputfile)

# --------------------------------------------------------------------------- #


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()

# That's all folk ;)
