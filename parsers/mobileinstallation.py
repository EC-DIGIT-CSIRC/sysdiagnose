#! /usr/bin/env python3

# For Python3
# Script to parse the swcutil_show.txt file
# Author: Emilien Le Jamtel

"""sysdiagnose intialize.

Usage:
  sysdiagnose-mobileinstallation.py -i <logfolder>
  sysdiagnose-mobileinstallation.py (-h | --help)
  sysdiagnose-mobileinstallation.py --version

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

parser_description = "Parsing mobile_installation logs file"
parser_input = "mobile_installation"  # list of log files
parser_call = "parsemobinstall"

# --------------------------------------------#


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'logs/MobileInstallation/mobile_installation.log*'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    return multilinelog.extract_from_file(path)


def parsemobinstall(loglist):
    events = {"events": []}
    for logfile in loglist:
        return multilinelog.extract_from_file(logfile)
    return events


def main():
    """
        Main function, to be called when used as CLI tool
    """

    arguments = docopt(__doc__, version='parser for mobile_installation log files v0.1')

    loglist = []

    if arguments['-i']:
        # list files in folder and build list object
        # loglist = glob.glob(arguments['<logfolder>'] + '/mobile_installation.log*')
        # events = parsemobinstall(loglist)
        try:
            loglist = glob.glob(arguments['<logfolder>'] + '/mobile_installation.log*')
            events = parsemobinstall(loglist)
            print(json.dumps(events, indent=4))
        except Exception as e:
            print(f'error retrieving log files. Reason: {str(e)}')
    # test

    return 0


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()
