#! /usr/bin/env python3

# For Python3
# Script to print from Accessibility TCC logs
# Author: david@autopsit.org

import os
import sys
from optparse import OptionParser

version_string = "sysdiagnose-Accessibility-TCC.py v2020-20-20 Version 1.0"

# ----- definition for parsing.py script -----#

parser_description = "Parsing Accessibility TCC logs"
parser_input = "Accessibility-TCC"
parser_call = "get_accessibility_tcc"

# --------------------------------------------#

# --------------------------------------------------------------------------- #


def get_accessibility_tcc(dbpath, ios_version=13):
    sys.path.append(os.path.abspath('../'))
    from utils import times
    from utils import sqlite2json

    tcc = sqlite2json.sqlite2struct(dbpath)
    return tcc
    # return sqlite2json.dump2json(tcc)


def print_accessibility_tcc(inputfile):
    sys.path.append(os.path.abspath('../'))
    from utils import times
    from utils import sqlite2json
    print(sqlite2json.dump2json(get_accessibility_tcc(inputfile)))
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
                      help="./logs/Accessibility/TCC.db to be parsed")
    (options, args) = parser.parse_args()

    # no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        exit(-1)

    print_accessibility_tcc(options.inputfile)

# --------------------------------------------------------------------------- #


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()

# That's all folk ;)
