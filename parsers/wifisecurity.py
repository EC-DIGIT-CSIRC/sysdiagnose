#! /usr/bin/env python3

# For Python3
# Script to print WIFI info from ./WiFi/security.txt
# Author: david@autopsit.org

import os
import sys
from optparse import OptionParser

version_string = "sysdiagnose-wifisecurity.py v2023-04-26 Version 1.0"

# ----- definition for parsing.py script -----#

parser_description = "Parsing WiFi Security logs"
parser_input = "wifisecurity"
parser_call = "get_wifi_security_log"

# --------------------------------------------#

# --------------------------------------------------------------------------- #


def get_log_files(log_root_path: str) -> list:
    """
        Get the list of log files to be parsed
    """
    log_files = [
        "WiFi/security.txt"
    ]
    return [os.path.join(log_root_path, log_files) for log_files in log_files]


def get_wifi_security_log(filepath, ios_version=16):
    """
        Parse ./WiFi/security.txt and extract block of interest:

            accc : <SecAccessControlRef: ck>
            acct : <WIFI SSID>
            agrp : apple
            cdat : 2023-02-09 21:10:38 +0000
            desc : <WIFI DESCRIPTION>
            labl : <WIFI LABEL>
            mdat : 2023-02-09 21:10:38 +0000
            musr : {length = 0, bytes = 0x}
            pdmn : ck
            sha1 : {length = 20, bytes = 0x98146b802675fb480dc64a8f3a7597ea70f03b46}
            svce : AirPort
            sync : 1
            tomb : 0
    """
    entries = []
    element = {}
    try:
        with open(filepath, "r") as f:
            for line in f:
                if ' : ' in line:
                    key, value = line.split(" : ")
                    # print(f"key: {key.strip()}, value: {value.strip()}")
                    element[key.strip()] = value.strip()
                elif element:
                    entries.append(element)
                    # print(f"appending {element}")
                    element = {}
    except Exception as e:
        print(f"Could not parse: {filepath}. Reason: {str(e)}")
    return entries


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
                      help="Wifi/security.txt to be parsed")
    (options, args) = parser.parse_args()

    # no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(-1)

    print(get_wifi_security_log(options.inputfile))

# --------------------------------------------------------------------------- #


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()

# That's all folk ;)
