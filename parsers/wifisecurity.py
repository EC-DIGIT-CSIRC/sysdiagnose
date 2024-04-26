#! /usr/bin/env python3

# For Python3
# Script to print WIFI info from ./WiFi/security.txt
# Author: david@autopsit.org

import os
import sys
import json
from optparse import OptionParser
import time
import struct
import datetime

version_string = "sysdiagnose-wifisecurity.py v2023-04-26 Version 1.0"

# ----- definition for parsing.py script -----#

parser_description = "Parsing WiFi Security logs"
parser_input = "wifisecurity"
parser_call = "get_wifi_security_log"

# --------------------------------------------#

# --------------------------------------------------------------------------- #


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
    wifi = []
    wifi_el = {}
    try:
        fd = open(filepath, "r")
        for line in fd:
            if line.startswith("accc"):
                wifi_el["accc"] = line.split(" : ")[1].strip()
            elif line.startswith("acct"):
                wifi_el["acct"] = line.split(" : ")[1].strip()
            elif line.startswith("agrp"):
                wifi_el["agrp"] = line.split(" : ")[1].strip()
            elif line.startswith("cdat"):
                wifi_el["cdat"] = line.split(" : ")[1].strip()
            elif line.startswith("desc"):
                wifi_el["desc"] = line.split(" : ")[1].strip()
            elif line.startswith("labl"):
                wifi_el["labl"] = line.split(" : ")[1].strip()
            elif line.startswith("mdat"):
                wifi_el["mdat"] = line.split(" : ")[1].strip()
            elif line.startswith("musr"):
                wifi_el["musr"] = line.split(" : ")[1].strip()
            elif line.startswith("pdmn"):
                wifi_el["pdmn"] = line.split(" : ")[1].strip()
            elif line.startswith("sha1"):
                wifi_el["sha1"] = line.split(" : ")[1].strip()
            elif line.startswith("svce"):
                wifi_el["svce"] = line.split(" : ")[1].strip()
            elif line.startswith("sync"):
                wifi_el["sync"] = line.split(" : ")[1].strip()
            elif line.startswith("tomb"):
                wifi_el["tomb"] = line.split(" : ")[1].strip()
            elif line == '\n':
                wifi.append(wifi_el)
                wifi_el = {}
        fd.close()
    except Exception as e:
        print(f"Could not parse: {filepath}. Reason: {str(e)}")
    return wifi


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
