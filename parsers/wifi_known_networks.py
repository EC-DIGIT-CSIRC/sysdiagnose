#! /usr/bin/env python3

# For Python3
# Script to print the values from WiFi/com.apple.wifi.known-networks.plist
# Author: aaron@lo-res.org, modeles after sysdiagnose-networkextension.py and mobileactivation.py
#
# Change log: Aaron Kaplan, initial version.

import sys
import json
import os
from optparse import OptionParser
from biplist import Uid, Data
from datetime import datetime
import glob
import misc


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Uid) or isinstance(obj, Data) or isinstance(obj, datetime):
            return str(obj)
        return super().default(obj)


version_string = "sysdiagnose_wifi_known_networks.py v2023-05-19 Version 1.0"

# ----- definition for parsing.py script -----#
# -----         DO NOT DELETE             ----#

parser_description = "Parsing Known Wifi Networks plist file"
parser_input = "wifi_data"
parser_call = "getKnownWifiNetworks"

# --------------------------------------------#


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'WiFi/com.apple.wifi.known-networks.plist'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    return misc.load_plist_file_as_json(path)


# --------------------------------------------------------------------------- #
# XXX #26 FIXME: this is obviously a very generic function and could be generalized and moved to misc/

def getKnownWifiNetworks(plistfiles=[], ios_version=13):
    """
    Print all the com.apple.wifi.known-networks.plist contents as JSON
    """
    result = {}
    for path in plistfiles:
        if os.path.basename(path) == "com.apple.wifi.known-networks.plist":
            try:
                result = misc.load_plist_file_as_json(path)
            except Exception as e:
                print(f"Could not parse {path}. Reason: {str(e)}", file=sys.stderr)
    return json.loads(json.dumps(result, indent=4, cls=CustomEncoder))


def main():
    """
        Main function, to be called when used as CLI tool
    """
    print(f"Running {version_string}\n")

    usage = "\n%prog -i inputfile\n"

    parser = OptionParser(usage=usage)
    parser.add_option("-i", dest="inputfile", action="store", type="string",            # XXX #35 FIXME! Here we should pass on a glob **.plist like in mobileactivation.py's main()
                      help="WiFi/com.apple.wifi.known-networks.plist To Be Searched")
    (options, args) = parser.parse_args()

    if options.inputfile:
        pl = getKnownWifiNetworks(options.inputfile)
        print(json.dumps(pl, indent=4, cls=CustomEncoder), file=sys.stderr)
    else:
        print("WARNING -i option is mandatory!", file=sys.stderr)


# --------------------------------------------------------------------------- #

if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()


# That's all folk ;)
