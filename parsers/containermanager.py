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
import re


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


# function copied from https://github.com/abrignoni/iOS-Mobile-Installation-Logs-Parser/blob/master/mib_parser.sql.py
# Month to numeric with leading zero when month < 10 function
# Function call: month = month_converter(month)


def month_converter(month):
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month = months.index(month) + 1
    if (month < 10):
        month = f"{month:02d}"
    return month

# Day with leading zero if day < 10 function
# Functtion call: day = day_converter(day)


def day_converter(day):
    day = int(day)
    if (day < 10):
        day = f"{day:02d}"
    return day
##


def parsecontainermanager(loglist):
    events = {"events": []}
    for logfile in loglist:
        with open(logfile, 'r', encoding="utf-8") as f:
            # multiline parsing with the following logic:
            # - build an entry with the seen lines
            # - upon discovery of a new entry, or the end of the file, consider the entry as complete and process the lines
            # - discovery of a new entry is done based on the timestamp, as each new entry starts this way
            prev_lines = []
            for line in f:
                timeregex = re.search(r"(?<=^)(.*?)(?= \[[0-9]+)", line)  # Regex for timestamp
                if timeregex:
                    # new entry, process the previous entry
                    if prev_lines:
                        new_entry = buildlogentry(''.join(prev_lines))
                        events['events'].append(new_entry)
                    # build the new entry
                    prev_lines = []
                    prev_lines.append(line)
                else:
                    # not a new entry, add the line to the previous entry
                    prev_lines.append(line)
            # process the last entry
            new_entry = buildlogentry(''.join(prev_lines))
            events['events'].append(new_entry)
            return events


def buildlogentry(line):
    entry = {}
    # timestamp
    timeregex = re.search(r"(?<=^)(.*?)(?= \[[0-9]+)", line)  # Regex for timestamp
    if timeregex:
        timestamp = timeregex.group(1)
        weekday, month, day, time, year = (str.split(timestamp[:24]))
        day = day_converter(day)
        month = month_converter(month)
        entry['timestamp'] = str(year) + '-' + str(month) + '-' + str(day) + ' ' + str(time)

        # log level
        loglevelregex = re.search(r"\<(.*?)\>", line)
        entry['loglevel'] = loglevelregex.group(1)

        # hex_ID
        hexIDregex = re.search(r"\(0x(.*?)\)", line)
        entry['hexID'] = '0x' + hexIDregex.group(1)

        # event_type
        eventyperegex = re.search(r"\-\[(.*)(\]\:)", line)
        if eventyperegex:
            entry['event_type'] = eventyperegex.group(1)

        # msg
        if 'event_type' in entry:
            msgregex = re.search(r"\]\:(.*)", line, re.MULTILINE | re.DOTALL)
            entry['msg'] = msgregex.group(1).strip()
        else:
            msgregex = re.search(r"\)\ (.*)", line, re.MULTILINE | re.DOTALL)
            entry['msg'] = msgregex.group(1).strip()

    return entry


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
