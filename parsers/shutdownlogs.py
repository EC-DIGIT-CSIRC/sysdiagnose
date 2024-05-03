#! /usr/bin/env python3

# For Python3
# Sysdiagnose Shutdown logs
# Author: Benoit Roussile

from optparse import OptionParser
import datetime
import glob
import os
import re
import sys

version_string = "sysdiagnose-shutdownlog.py v2024-01-11 Version 1.0"

# ----- definition for parsing.py script -----#

parser_description = "Parsing shutdown.log file"
parser_input = "shutdownlog"
parser_call = "parse_shutdownlog"

# --------------------------------------------#

CLIENTS_ARE_STILL_HERE_LINE = "these clients are still here"
REMAINING_CLIENT_PID_LINE = "remaining client pid"
SIGTERM_LINE = "SIGTERM"

# --------------------------------------------------------------------------- #


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'system_logs.logarchive/Extra/shutdown.log'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_shutdownlog(filepath, ios_version=16):
    """
        This is the function that will be called
    """
    # read log file content
    log_lines = ""
    with open(filepath, "r") as f:
        log_lines = f.readlines()

    json_object = {}
    parsed_data = {}
    index = 0
    # go through log file
    while index < len(log_lines):
        # look for begining of shutdown sequence
        if CLIENTS_ARE_STILL_HERE_LINE in log_lines[index]:
            running_processes = []
            while not (SIGTERM_LINE in log_lines[index]):
                if (REMAINING_CLIENT_PID_LINE in log_lines[index]):
                    result = re.search(r".*: (\b\d+) \((.*)\).*", log_lines[index])
                    pid = result.groups()[0]
                    binary_path = result.groups()[1]
                    process = pid + ":" + binary_path
                    if not (process in running_processes):
                        running_processes.append(process)
                index += 1
            # compute timestamp from SIGTERM line
            result = re.search(r".*\[(\d+)\].*", log_lines[index])
            timestamp = result.groups()[0]
            time = str(datetime.datetime.fromtimestamp(int(timestamp), datetime.UTC))
            # add entries
            parsed_data[time] = []
            for p in running_processes:
                parsed_data[time].append({"pid": p.split(":")[0], "path": p.split(":")[1]})
        index += 1

    json_object["data"] = parsed_data

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
                      help="path to the shutdown.log file")
    (options, args) = parser.parse_args()

    # no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(-1)

    # Call the demo function when called directly from CLI
    print(parse_shutdownlog(options.inputfile))

# --------------------------------------------------------------------------- #


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()

# That's all folk ;)
