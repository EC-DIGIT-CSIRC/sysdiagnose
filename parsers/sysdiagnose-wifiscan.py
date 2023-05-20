#! /usr/bin/env python3

# For Python3
# Script to parse the swcutil_show.txt file
# Author: Emilien Le Jamtel

"""sysdiagnose intialize.

Usage:
  sysdiagnose-wifiscan.py -i <logfolder>
  sysdiagnose-wifiscan.py (-h | --help)
  sysdiagnose-wifiscan.py --version

Options:
  -h --help     Show this screen.
  -v --version     Show version.
"""

import sys
from optparse import OptionParser
import plistlib
import json
from docopt import docopt
import glob
import re

# ----- definition for parsing.py script -----#

parser_description = "Parsing wifi_scan files"
parser_input = "wifi_data"  # list of log files - only get the .txt files from the list
parser_call = "parsewifiscan"

# --------------------------------------------------------------------------- #

def parsewifiscan(wifi_data):
    output = []
    for data in wifi_data:
        if data.endswith('.txt'):
            print('parsing: ' + data)
            with open(data, 'r') as f:
                for line in f:
                    if line.strip():
                        content = line.split(',')
                        # check if the first entry of the dict contains the ssid
                        if 'ssid=' in content[0]:
                            parsed_data = {}
                            for item in content:
                                key_value = item.split("=")
                                parsed_data[key_value[0].strip()] = key_value[1]
                            # cleaning SSID entries
                            for key in parsed_data.copy().keys():
                                if ' - ssid' in key:
                                    up_parsed_data = {'ssid': re.sub(' - ssid', '', key), 'ssid_hex': parsed_data[key]}
                                    del parsed_data[key]
                                    up_parsed_data.update(parsed_data)
                                    parsed_data = up_parsed_data
                            output.append(parsed_data)
    return output

# --------------------------------------------------------------------------- #

def main():
    """
        Main function, to be called when used as CLI tool
    """

    arguments = docopt(__doc__, version='parser for wifi_scan files v0.3')

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
