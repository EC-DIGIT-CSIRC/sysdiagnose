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

import sys
from optparse import OptionParser
import plistlib
import json
from docopt import docopt
from tabulate import tabulate
import glob
import re


# ----- definition for parsing.py script -----#

parser_description = "Parsing containermanagerd logs file"
parser_input = "container_manager"  # list of log files
parser_call = "parsecontainermanager"

# --------------------------------------------#

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
        file = open(logfile, 'r', encoding='utf8')
        for line in file:
            # getting Timestamp - adding entry only if timestamp is present
            timeregex = re.search(r"(?<=^)(.*)(?= \[)", line)  # Regex for timestamp
            if timeregex:
                new_entry = buildlogentry(line)
                events['events'].append(new_entry)
    return events


def buildlogentry(line):
    entry = {}
    # timestamp
    timeregex = re.search(r"(?<=^)(.*)(?= \[[0-9]+)", line)  # Regex for timestamp
    if timeregex:
        timestamp = timeregex.group(1)
        weekday, month, day, time, year = (str.split(timestamp[:24]))
        day = day_converter(day)
        month = month_converter(month)
        entry['timestamp'] = str(year)+ '-'+ str(month) + '-' + str(day) + ' ' + str(time)

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
            msgregex = re.search(r"\]\:(.*)", line)
            entry['msg'] = msgregex.group(1)
        else:
            msgregex = re.search(r"\)\ (.*)", line)
            entry['msg'] = msgregex.group(1)

    return entry


def main():
    """
        Main function, to be called when used as CLI tool
    """
    # Parse arguments
    arguments = docopt(__doc__, version='parser for container manager log files v0.1')

    loglist=[]

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
