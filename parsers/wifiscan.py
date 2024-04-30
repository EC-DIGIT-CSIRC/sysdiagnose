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

import json
from docopt import docopt
import glob
import re

# ----- definition for parsing.py script -----#

parser_description = "Parsing wifi_scan files"
parser_input = "wifi_data"  # list of log files - only get the .txt files from the list
parser_call = "parsewifiscan"

# --------------------------------------------------------------------------- #


def parsewifiscan(wifi_data: list):
    output = []
    for data in wifi_data:
        if data.endswith('.txt'):
            print('parsing: ' + data)
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
                        # key = first place with =
                        #  check what is after =, if normal char then value is until next ,
                        #                         if [ then value is until ]
                        #                         if { then value is until }
                        # first ssid and ssid_hex
                        m = re.match(r"'(?P<ssid>[^\']+)' \((?P<ssid_hex>[^\)]+)\)", line)
                        parsed_data['ssid'] = m.group('ssid')
                        parsed_data['ssid_hex'] = m.group('ssid_hex')
                        index_now = line.index(',') + 1
                        # now the rest
                        while index_now < len(line):
                            index_equals = line.index('=', index_now)
                            key = line[index_now:index_equals].strip()
                            if line[index_equals + 1] in ['[']:
                                index_close = line.index(']', index_now)
                                value = line[index_equals + 2:index_close].strip()
                            else:
                                index_close = line.index(',', index_now)
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
