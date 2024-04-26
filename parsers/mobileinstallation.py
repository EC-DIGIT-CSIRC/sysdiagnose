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

import sys
from optparse import OptionParser
import plistlib
import json
from docopt import docopt
from tabulate import tabulate
import glob
import re


# ----- definition for parsing.py script -----#
# -----         DO NOT DELETE             ----#

parser_description = "Parsing mobile_installation logs file"
parser_input = "mobile_installation"  # list of log files
parser_call = "parsemobinstall"

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


def parsemobinstall(loglist):
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
    print(line)
    timeregex = re.search(r"(?<=^)(.*)(?= \[[0-9]+)", line)  # Regex for timestamp
    timestamp = timeregex.group(1)
    print(timestamp)
    weekday, month, day, time, year = (str.split(timestamp))
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

    arguments = docopt(__doc__, version='parser for mobile_installation log files v0.1')

    loglist=[]

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
