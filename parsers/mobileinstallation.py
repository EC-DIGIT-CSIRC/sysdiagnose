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
import re


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
        with open(logfile, 'r', encoding='utf8') as f:
            prev_lines = []
            for line in f:
                line = line.strip()
                # support multiline entries
                if line.endswith('{'):
                    prev_lines.append(line)
                    continue
                if prev_lines:
                    prev_lines.append(line)
                    if line.endswith('}'):
                        line = ''.join(prev_lines)
                        prev_lines = []
                    else:
                        continue
                # normal or previously multiline entry
                # getting Timestamp - adding entry only if timestamp is present
                timeregex = re.search(r"(?<=^)(.*)(?= \[)", line)  # Regex for timestamp
                if timeregex:
                    new_entry = buildlogentry(line)
                    events['events'].append(new_entry)
    return events


def buildlogentry(line):
    try:
        entry = {}
        # timestamp
        timeregex = re.search(r"(?<=^)(.*?)(?= \[[0-9]+)", line)  # Regex for timestamp
        timestamp = timeregex.group(1)
        weekday, month, day, time, year = (str.split(timestamp))
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
            msgregex = re.search(r"\]\:(.*)", line)
            entry['msg'] = msgregex.group(1).strip()
        else:
            msgregex = re.search(r"\)\ (.*)", line)
            entry['msg'] = msgregex.group(1).strip()
    except Exception as e:
        print(f"Error parsing line: {line}. Reason: {str(e)}")
        raise Exception from e

    return entry


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
