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

parser_description = "Parsing mobileactivation logs file"
parser_input = "mobile_activation"  # list of log files
parser_call = "parsemobactiv"

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


def parsemobactiv(loglist):
    events = {"events": []}
    for logfile in loglist:
        file = open(logfile, 'r', encoding='utf8')
        # init
        status = ''

        for line in file:
            # init
            if "____________________ Mobile Activation Startup _____________________" in line.strip():
                status = 'act_start'
                act_lines = []
            elif "____________________________________________________________________" in line.strip() and status == 'act_start':
                status = 'act_stop'
                events['events'].append(buildlogentry_actentry(act_lines))
            elif status == 'act_start':
                act_lines.append(line.strip())
            elif "<notice>" in line.strip():
                buildlogentry_notice(line.strip())
    # print(json.dumps(events,indent=4))
    return events


def buildlogentry_actentry(lines):
    # print(lines)
    event = {'loglevel': 'debug'}
    # get timestamp
    timeregex = re.search(r"(?<=^)(.*)(?= \[)", lines[0])
    timestamp = timeregex.group(1)
    weekday, month, day, time, year = (str.split(timestamp))
    day = day_converter(day)
    month = month_converter(month)
    event['timestamp'] = str(year)+ '-'+ str(month) + '-' + str(day) + ' ' + str(time)

    # build event
    for line in lines:
        splitted = line.split(":")
        if len(splitted) > 1:
            event[splitted[-2].strip()] = splitted[-1].strip()

    return event


def buildlogentry_notice(line):
    event = {'loglevel': 'notice'}
    # get timestamp
    timeregex = re.search(r"(?<=^)(.*)(?= \[)", line)
    timestamp = timeregex.group(1)
    weekday, month, day, time, year = (str.split(timestamp))
    day = day_converter(day)
    month = month_converter(month)
    event['timestamp'] = str(year)+ '-'+ str(month) + '-' + str(day) + ' ' + str(time)

    # hex_ID
    hexIDregex = re.search(r"\(0x(.*?)\)", line)
    event['hexID'] = '0x' + hexIDregex.group(1)

    # event_type
    eventyperegex = re.search(r"\-\[(.*)(\]\:)", line)
    if eventyperegex:
        event['event_type'] = eventyperegex.group(1)

    # msg
    if 'event_type' in event:
        msgregex = re.search(r"\]\:(.*)", line)
        event['msg'] = msgregex.group(1)
    else:
        msgregex = re.search(r"\)\ (.*)", line)
        event['msg'] = msgregex.group(1)

    return event


def main():
    """
        Main function, to be called when used as CLI tool
    """

    arguments = docopt(__doc__, version='parser for mobile_installation log files v0.1')

    loglist=[]

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
