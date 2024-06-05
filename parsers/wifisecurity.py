#! /usr/bin/env python3

# For Python3
# Script to print WIFI info from ./WiFi/security.txt
# Author: david@autopsit.org

import os

parser_description = "Parsing WiFi Security logs"


def get_log_files(log_root_path: str) -> list:
    """
        Get the list of log files to be parsed
    """
    log_files = [
        "WiFi/security.txt"
    ]
    return [os.path.join(log_root_path, log_files) for log_files in log_files]


def parse_path(path: str) -> list | dict:
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
        with open(get_log_files(path)[0], "r") as f:
            for line in f:
                if ' : ' in line:
                    key, value = line.split(" : ")
                    # print(f"key: {key.strip()}, value: {value.strip()}")
                    element[key.strip()] = value.strip()
                elif element:
                    entries.append(element)
                    # print(f"appending {element}")
                    element = {}
    except IndexError:
        return {'error': 'No WiFi/security.txt file present'}
    except Exception as e:
        print(f"Could not parse: {get_log_files(path)[0]}. Reason: {str(e)}")
    return entries
