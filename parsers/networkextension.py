#! /usr/bin/env python3

# For Python3
# Script to extract the values from logs/Networking/com.apple.networkextension.plist
# Author: Emilien Le Jamtel

"""sysdiagnose intialize.

Usage:
  sysdiagmose-networkextension.py -i <file>
  sysdiagmose-networkextension.py (-h | --help)
  sysdiagmose-networkextension.py --version

Options:
  -h --help     Show this screen.
  -v --version     Show version.
"""

# import sys
# from optparse import OptionParser
# import plistlib
import misc
# import json
from docopt import docopt
from tabulate import tabulate
import os
import glob


# ----- definition for parsing.py script -----#
# -----         DO NOT DELETE             ----#

parser_description = "Parsing networkextension plist file"
parser_input = "networkextension"
parser_call = "parseplist"

# --------------------------------------------#


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'logs/Networking/com.apple.networkextension.plist'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parseplist(fname):
    return misc.load_plist_file_as_json(fname)


def main():
    """
        Main function, to be called when used as CLI tool
    """

    arguments = docopt(__doc__, version='parser for networkextension.plist v0.1')

    if arguments['-i']:
        try:
            objects = parseplist(arguments['<file>'])

            headers = ['Interesting extracted object']
            lines = []
            for object in objects['objects']:
                line = [object]
                lines.append(line)
            print(tabulate(lines, headers=headers))
        except Exception as e:
            print(f'Error: {str(e)}')

    # parseplist("../data/1/sysdiagnose_2019.02.13_15-50-14+0100_iPhone_OS_iPhone_16C101/logs/Networking/com.apple.networkextension.plist")

    return 0


# --------------------------------------------------------------------------- #

"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()


# That's all folk ;)
