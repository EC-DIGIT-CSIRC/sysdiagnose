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
import misc
import os
import re

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
        with open(logfile, 'r', encoding='utf8') as f:
            status = None  # status tracker for multiline parsing
            for line in f:
                # Activation multiline parsing
                if not status and "____________________ Mobile Activation Startup _____________________" in line:
                    status = 'act_start'
                    act_lines = []
                elif status == 'act_start' and "____________________________________________________________________" in line:
                    status = None
                    events['events'].append(buildlogentry_actentry(act_lines))
                elif status == 'act_start':
                    act_lines.append(line.strip())
                # plist multiline parsing
                elif line.strip().endswith(":"):  # next line will be starting with <?xml
                    status = 'plist_start'
                    plist_lines = {
                        'line': line.strip(),
                        'plist': []
                    }
                elif status == 'plist_start':
                    plist_lines['plist'].append(line.encode())
                    if line.strip() == '</plist>':  # end of plist
                        status = None
                        # end of plist, now need to parse the line and plist
                        event = buildlogentry_other(plist_lines['line'])
                        event['plist'] = misc.load_plist_string_as_json(b''.join(plist_lines['plist']))
                        # LATER parse the plist
                        # - extract the recursive plist
                        # - decode the certificates into nice JSON
                        # - and so on with more fun for the future
                        events['events'].append(event)
                elif line.strip() != '':
                    events['events'].append(buildlogentry_other(line.strip()))
    # print(json.dumps(events,indent=4))
    return events


def buildlogentry_actentry(lines):
    # print(lines)
    event = {'loglevel': 'debug'}
    # get timestamp
    timeregex = re.search(r"(?<=^)(.*?)(?= \[)", lines[0])
    timestamp = timeregex.group(1)
    weekday, month, day, time, year = (str.split(timestamp))
    day = day_converter(day)
    month = month_converter(month)
    event['timestamp'] = str(year) + '-' + str(month) + '-' + str(day) + ' ' + str(time)

    # hex_ID
    hexIDregex = re.search(r"\(0x(.*?)\)", lines[0])
    event['hexID'] = '0x' + hexIDregex.group(1)

    # build event
    for line in lines:
        splitted = line.split(":")
        if len(splitted) > 1:
            event[splitted[-2].strip()] = splitted[-1].strip()

    return event


def buildlogentry_other(line):
    event = {}
    try:
        # get timestamp
        timeregex = re.search(r"(?<=^)(.*?)(?= \[)", line)
        timestamp = timeregex.group(1)
        weekday, month, day, time, year = (str.split(timestamp))
        day = day_converter(day)
        month = month_converter(month)
        event['timestamp'] = str(year) + '-' + str(month) + '-' + str(day) + ' ' + str(time)

        # log level
        loglevelregex = re.search(r"\<(.*?)\>", line)
        event['loglevel'] = loglevelregex.group(1)

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
            event['msg'] = msgregex.group(1).strip()
        else:
            msgregex = re.search(r"\)\ (.*)", line)
            event['msg'] = msgregex.group(1).strip()
    except Exception as e:
        print(f"Error parsing line: {line}. Reason: {str(e)}")
        raise Exception from e

    return event


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
