#! /usr/bin/env python3

# For Python3
# Demo blank parsers
# Author: david@autopsit.org

import os
import sys
import json
from optparse import OptionParser
import time
import struct
import datetime

version_string = "sysdiagnose-demo-parser.py v2023-04-26 Version 1.0"

# ----- definition for parsing.py script -----#

parser_description = "Demo parsers"
parser_input = "demo_input_file"
parser_call = "demo_function"

# --------------------------------------------#

# --------------------------------------------------------------------------- #


def demo_function(filepath, ios_version=16):
    """
        This is the function that will be called
    """
    json_object = {}
    return json_object


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
                      help="Demo file to use")
    (options, args) = parser.parse_args()

    # no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(-1)

    # Call the demo function when called directly from CLI
    print(demo_function(options.inputfile))

# --------------------------------------------------------------------------- #


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()

# That's all folk ;)
