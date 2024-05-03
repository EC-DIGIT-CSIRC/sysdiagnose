#! /usr/bin/env python3

# For Python3
# Script to parse the swcutil_show.txt file
# Author: Emilien Le Jamtel

"""sysdiagnose intialize.

Usage:
  sysdiagnose-mobileactivation.py -i <logfolder>
  sysdiagnose-mobileactivation.py (-h | --help)
  sysdiagnose-mobileactivation.py --version

Options:
  -h --help     Show this screen.
  -v --version     Show version.
"""

from docopt import docopt
import glob
import json
import os
from utils import multilinelog

# ----- definition for parsing.py script -----#
# -----         DO NOT DELETE             ----#

parser_description = "Parsing mobileactivation logs file"
parser_input = "mobile_activation"  # list of log files
parser_call = "parsemobactiv"

# --------------------------------------------#


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'logs/MobileActivation/mobileactivationd.log*'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parsemobactiv(loglist):
    for logfile in loglist:
        return multilinelog.extract_from_file(logfile)


def main():
    """
        Main function, to be called when used as CLI tool
    """

    arguments = docopt(__doc__, version='parser for mobile_installation log files v0.1')

    loglist = []

    if arguments['-i']:
        # list files in folder and build list object
        # try:
        loglist = glob.glob(arguments['<logfolder>'] + '/mobileactivationd.log*')
        print(json.dumps(parsemobactiv(loglist), indent=4))

    return 0


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()
