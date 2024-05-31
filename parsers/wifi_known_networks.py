#! /usr/bin/env python3

# For Python3
# Script to print the values from WiFi/com.apple.wifi.known-networks.plist
# Author: aaron@lo-res.org, modeles after sysdiagnose-networkextension.py and mobileactivation.py
#
# Change log: Aaron Kaplan, initial version.

import os
import glob
import misc


parser_description = "Parsing Known Wifi Networks plist file"


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


'''
code usefull for future printing function

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Uid) or isinstance(obj, Data) or isinstance(obj, datetime):
            return str(obj)
        return super().default(obj)


        pl = getKnownWifiNetworks(options.inputfile)
        print(json.dumps(pl, indent=4, cls=CustomEncoder), file=sys.stderr)
'''
