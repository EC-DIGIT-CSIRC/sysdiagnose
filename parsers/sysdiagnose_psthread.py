#! /usr/bin/env python3

# For Python3
# Script to parse ps.txt to ease parsing
# Author: david@autopsit.org
#
# TODO define output
# - json
# - tree structure
# - simplified
#
import re
import sys
import json
from optparse import OptionParser

version_string = "sysdiagnose_ps.py Version 1.0"

# ----- definition for parsing.py script -----#
# -----         DO NET DELETE             ----#

parser_description = "Parsing ps_thread.txt file"
parser_input = "ps_thread"
parser_call = "parse_ps_thread"

# --------------------------------------------#


def parse_ps_thread(filename, ios_version=13):
    fd = open(filename, "r")
    input = fd.readlines()
    input_clean = []
    for line in input:
        if "??" in line:
            input_clean.append(line)
    headers = [h for h in ' '.join(input[0].strip().split()).split() if h]
    raw_data = map(lambda s: s.strip().split(None, len(headers) -1), input_clean)
    return [dict(zip(headers, r)) for r in raw_data]


# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #


"""
    Main function
"""


def main():

    print(f"Running {version_string}\n")

    usage = "\n%prog -i inputfile\n"

    parser = OptionParser(usage=usage)
    parser.add_option("-i", dest="inputfile",
                      action="store", type="string",
                      help="ps.txt")
    (options, args) = parser.parse_args()

    # no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(-1)

    # parse PS file :)
    if options.inputfile:
        processes = parse_ps_thread(options.inputfile)
        print(json.dumps(processes, indent=4))
        # export_as_tree(processes, True)
    else:
        print("WARNING -i option is mandatory!")


# --------------------------------------------------------------------------- #

"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()


# That's all folk ;)
