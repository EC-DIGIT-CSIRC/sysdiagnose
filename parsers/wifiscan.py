#! /usr/bin/env python3

"""sysdiagnose intialize.

Usage:
  sysdiagnose-wifiscan.py -i <logfolder>
  sysdiagnose-wifiscan.py (-h | --help)
  sysdiagnose-wifiscan.py --version

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

parser_description = "Parsing wifi_scan files"
parser_input = "wifi_data"  # list of log files - only get the .txt files from the list
parser_call = "parsewifiscan"

# --------------------------------------------------------------------------- #


def get_log_files(log_root_path: str) -> list:
    log_files = [
        "WiFi/wifi_scan.txt"
    ]

    return [os.path.join(log_root_path, log_files) for log_files in log_files]


def parsewifiscan(wifi_data: list):
    output = []
    for data in wifi_data:
        if data.endswith('.txt'):
            with open(data, 'r') as f:
                for line in f:
                    line = line.strip()
                    # skip empty lines
                    if not line:
                        continue
                    parsed_data = {}
                    # process header
                    if line.startswith('total='):
                        items = line.split(',')
                        for item in items:
                            key, value = item.split('=')
                            parsed_data[key.strip()] = value.strip()
                    else:
                        # extract key-value by string

                        # first ssid and ssid_hex, but need to detect the type first
                        regexes = [
                            # iOS 16 and later: FIRSTCONWIFI - ssid=4649525354434f4e57494649
                            r"(?P<ssid>.+?) - ssid=(?P<ssid_hex>[^,]+)",
                            # iOS 15: 'FIRSTCONWIFI' (4649525354434f4e57494649)
                            r"'(?P<ssid>[^\']+)' \((?P<ssid_hex>[^\)]+)\)"
                        ]
                        for regex in regexes:
                            m = re.match(regex, line)
                            if m:
                                parsed_data['ssid'] = m.group('ssid')
                                parsed_data['ssid_hex'] = m.group('ssid_hex')
                                break
                        # key = first place with =
                        #  check what is after =, if normal char then value is until next ,
                        #                         if [ then value is until ]
                        #                         if { then value is until }
                        index_now = line.index(',') + 1
                        # now the rest of the line
                        while index_now < len(line):
                            index_equals = line.index('=', index_now)
                            key = line[index_now:index_equals].strip()
                            if line[index_equals + 1] in ['[']:
                                index_close = line.index(']', index_now)
                                value = line[index_equals + 1:index_close].strip()
                            else:
                                try:
                                    index_close = line.index(',', index_now)
                                except ValueError:  # catch end of line
                                    index_close = len(line)
                                value = line[index_equals + 1:index_close].strip()
                            index_now = index_close + 2
                            parsed_data[key] = value
                    output.append(parsed_data)
    return output

# --------------------------------------------------------------------------- #


def main():
    """
        Main function, to be called when used as CLI tool
    """

    arguments = docopt(__doc__, version='parser for wifi_scan files v0.4')

    if arguments['-i']:
        # list scan files in folder and build a list
        scanlist = glob.glob(arguments['<logfolder>'] + '/wifi_scan*.txt')
        output = parsewifiscan(scanlist)
        print(json.dumps(output, indent=4))

# --------------------------------------------------------------------------- #


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()

# That's all folk ;)
