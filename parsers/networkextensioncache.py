#! /usr/bin/env python3

# For Python3
# Script to extract the values from logs/Networking/com.apple.networkextension.plist
# Author: Emilien Le Jamtel

"""sysdiagnose intialize.

Usage:
  sysdiagmose-networkextensioncache.py -i <file>
  sysdiagmose-networkextensioncache.py (-h | --help)
  sysdiagmose-networkextensioncache.py --version

Options:
  -h --help     Show this screen.
  -v --version     Show version.
"""

from docopt import docopt
from tabulate import tabulate
import glob
import os
import misc


# ----- definition for parsing.py script -----#
# -----         DO NOT DELETE             ----#

parser_description = "Parsing networkextensioncache plist file"
parser_input = "networkextensioncache"
parser_call = "parseplist"

# --------------------------------------------#


def get_log_files(log_root_path: str) -> list:
    # FIXME it looks like there are no files matching the criteria
    log_files_globs = [
        'logs/Networking/com.apple.networkextension.cache.plist'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parseplist(fname):
    pl = misc.load_plist_file_as_json(fname)

    # pprint.pprint(pl)

    return pl['app-rules']

    # objects = pl['$objects']

    # output = {'objects':[]}

    # for object in objects:
    #    if type(object) == str:
    #        output['objects'].append(object)


def main():
    """
        Main function, to be called when used as CLI tool
    """

    arguments = docopt(__doc__, version='parser for networkextensioncache.plist v0.1')

    # ## test
    # if arguments['-i'] == True:
    #    parseplist(arguments['<file>'])
    #    sys.exit()
    # ## test

    if arguments['-i']:
        try:
            apprules = parseplist(arguments['<file>'])

            headers = ['App', 'UUIDs']
            lines = []
            for key, val in apprules.items():
                line = [key, val]
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
