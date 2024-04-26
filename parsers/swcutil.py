#! /usr/bin/env python3

# For Python3
# Script to parse the swcutil_show.txt file
# Author: Emilien Le Jamtel

"""sysdiagnose intialize.

Usage:
  sysdiagnose-swcutil.py -i <file>
  sysdiagnose-swcutil.py (-h | --help)
  sysdiagnose-swcutil.py --version

Options:
  -h --help     Show this screen.
  -v --version     Show version.
"""

import sys
from optparse import OptionParser
import plistlib
import json
from docopt import docopt
from tabulate import tabulate


# ----- definition for parsing.py script -----#
# -----         DO NOT DELETE             ----#

parser_description = "Parsing swcutil_show file"
parser_input = "swcutil_show"
parser_call = "parseswcutil"

# --------------------------------------------#


def parseswcutil(file):
    with open(file, 'r') as f_in:
        # init section
        headers = []
        db = []
        network = []
        settings = []
        memory = []
        status = 'headers'

        # stripping
        for line in f_in:
            if line.strip() == "":
                continue
            if line.strip() == "=================================== DATABASE ===================================":
                status = 'db'
                continue
            elif line.strip() == "=================================== NETWORK ====================================":
                status = 'network'
                continue
            elif line.strip() == "=================================== SETTINGS ===================================":
                status = 'settings'
                continue
            elif line.strip() == "================================= MEMORY USAGE =================================":
                status = 'memory'
                continue
            elif status == 'headers':
                headers.append(line.strip())
                continue
            elif status == 'db':
                db.append(line.strip())
                continue
            elif status == 'network':
                network.append(line.strip())
                continue
            elif status == 'settings':
                settings.append(line.strip())
                continue
            elif status == 'memory':
                memory.append(line.strip())
                continue

        # call parsing function per section
        parsed_headers = parse_basic(headers)
        parsed_db = parse_db(db)
        parsed_network = parse_basic(network)
        parsed_settings = parse_basic(settings)
        parsed_memory = parse_basic(memory)

    return {'headers': parsed_headers, 'db': parsed_db, 'network': parsed_network, 'settings': parsed_settings, 'memory': parsed_memory}


def parse_basic(data):
    output = {}
    for line in data:
        splitted = line.split(":", 1)
        if len(splitted) > 1:
            output[splitted[0]] = splitted[1].strip()
    return output


def parse_db(data):
    # init
    db = []
    db_data = []
    for line in data:
        if line.strip() == "--------------------------------------------------------------------------------":
            db.append(parse_basic(db_data))
            db_data = []
        else:
            db_data.append(line.strip())
    return db


def main():
    """
        Main function, to be called when used as CLI tool
    """

    arguments = docopt(__doc__, version='parser for networkextension.plist v0.1')

    ### test
    if arguments['-i']:
        # Output is good enough, just print
        with open(arguments['<file>'], 'r') as f_in:
            for line in f_in:
                print(line.strip())
        # parseswcutil(arguments['<file>'])
        sys.exit()
    ### test

    return 0


# --------------------------------------------------------------------------- #

"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()


# That's all folk ;)
