#! /usr/bin/env python3

# For Python3
# Script to print the values from logs/tailspindb/UUIDToBinaryLocations (XML plist)
# Uses Python3's plistlib
# Author: cheeky4n6monkey@gmail.com
#
# Change log: David DURVAUX - add function are more granular approach

import sys
import json
import pprint
import plistlib
from optparse import OptionParser

version_string = "sysdiagnose-uuid2path.py v2020-02-07 Version 2.0"

# ----- definition for parsing.py script -----#
# -----         DO NET DELETE             ----#

parser_description = "Parsing UUIDToBinaryLocations plist file"
parser_input = "UUIDToBinaryLocations"
parser_call = "getUUID2path"

# --------------------------------------------#

# --------------------------------------------------------------------------- #


def getUUID2path(filename, ios_version=13):
    try:
        with open(filename, 'rb') as fp:
            pl = plistlib.load(fp)
            uuid2path = {}
            for uuid, path in pl.items():
                if uuid in uuid2path.keys():
                    print("WARNING: duplicate UUID found!!")
                uuid2path[uuid] = path
            fp.close()
            return uuid2path
    except Exception as e:
        print("Impossible to parse %s: %s" % (filename, str(e)))
    return None


def printResult(json):
    """
        Print the hashtable produced by getUUID2Path to console as UUID, path
    """
    if json:
        for uuid in json.keys():
            print("%s, %s" % (str(uuid), str(json[uuid])))
    print("\n %s GUIDs found\n" % str(len(json.keys())))
    return


def export_to_json(_dict, filename="./uuid2path.json"):
    data = json.dumps(_dict, indent=4)
    try:
        with open(filename, "w") as fd:
            json.dump(data, fd)
    except Exception as e:
        print(f"Could not dump the JSON dict to {filename}. Reason: {str(e)}\n")
    return


def exportToMISP(json):     # XXX FIXME: to be deleted . Should be not in the parser
    """
        export the UUID and path to MISP

        TODO -  implement ;)
    """
    print("NOT IMPLEMENTED")
    return


def main():
    if sys.version_info[0] < 3:
        print("Must be using Python 3! Exiting ...")
        exit(-1)

    usage = "\n%prog -i inputfile\n"

    parser = OptionParser(usage=usage)
    parser.add_option("-i", dest="inputfile",
                      action="store", type="string",
                      help="logs/tailspindb/UUIDToBinaryLocations plist To Be Printed")
    (options, args) = parser.parse_args()

    # no arguments given by user, print help and exit
    if options.inputfile:
        print("Running " + version_string + "\n")
        printResult(getUUID2path(options.inputfile))
    else:
        parser.print_help()
        exit(-1)
    return


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()


# That's all folk ;)
