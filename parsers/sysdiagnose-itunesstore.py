#! /usr/bin/env python3

# For Python3
# Script to print from iTunes Store
# Author: david@autopsit.org

import os
import sys
import json
from optparse import OptionParser

version_string = "sysdiagnose-itunesstore.py v2020-20-19 Version 1.0"

# ----- definition for parsing.py script -----#
# -----         DO NET DELETE             ----#

parser_description = "Parsing iTunes store logs"
parser_input = "itunesstore"
parser_call = "get_itunesstore"

# --------------------------------------------#

# --------------------------------------------------------------------------- #


def get_itunesstore(dbpath, ios_version=13):
    sys.path.append(os.path.abspath('../'))
    from utils import times
    from utils import sqlite2json

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
