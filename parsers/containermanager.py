#! /usr/bin/env python3

# For Python3
# Script to parse the swcutil_show.txt file
# Author: Emilien Le Jamtel

"""sysdiagnose intialize.

Usage:
  sysdiagnose-containermanager.py -i <logfolder>
  sysdiagnose-containermanager.py (-h | --help)
  sysdiagnose-containermanager.py --version

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

parser_description = "Parsing containermanagerd logs file"
parser_input = "container_manager"  # list of log files
parser_call = "parsecontainermanager"

# --------------------------------------------#


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'logs/MobileContainerManager/containermanagerd.log*'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parsecontainermanager(loglist):
    for logfile in loglist:
        return multilinelog.extract_from_file(logfile)


def main():
    """
        Main function, to be called when used as CLI tool
    """
    # Parse arguments
    arguments = docopt(__doc__, version='parser for container manager log files v0.1')

    loglist = []

    if arguments['-i']:
        # list files in folder and build list object
        # try:
        loglist = glob.glob(arguments['<logfolder>'] + '/containermanagerd.log*')
        events = parsecontainermanager(loglist)
        print(json.dumps(events, indent=4))
        # except:
        #    print("error retrieving log files")
    # test

    return 0


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()
