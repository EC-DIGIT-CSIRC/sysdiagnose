#! /usr/bin/env python3

# For Python3
# Script to print the values from /logs/SystemVersion/SystemVersion.plist
# Author: cheeky4n6monkey@gmail.com
#
# Change log: David DURVAUX - add function are more granular approach

import sys
from optparse import OptionParser
import plistlib

version_string = "sysdiagnose-sys.py v2019-05-10 Version 2.0"

# ----- definition for parsing.py script -----#
# -----         DO NET DELETE             ----#

parser_description = "Parsing SystemVersion plist file"
parser_input = "systemversion"
parser_call = "getProductInfo"

# --------------------------------------------#


# --------------------------------------------------------------------------- #

def getProductInfo(path="./logs/SystemVersion/SystemVersion.plist", ios_version=13):
    """
        return an hash table with  the following structure
        {
            "ProductName" : "",
            "ProductionVersion" : "",
            "ProductBuildVersion" : ""
        }
        Non populated field are filled with a None value
    """
    result = {
        "ProductName": None,
        "ProductionVersion": None,
        "ProductBuildVersion": None
    }
    try:
        fd = open(path, 'rb')
        plist = plistlib.load(fd)
        for key in ["ProductName", "ProductVersion", "ProductBuildVersion", "BuildID", "SystemImageID"]:
            if key in plist.keys():
                result[key] = plist[key]
            else:
                print("WARNING: %s not found in %s plist" % (key, path))
        fd.close()
    except Exception as e:
        print("Impossible to parse %s: %s" % (path, str(e)))
    return result


def main():
    """
        Main function, to be called when used as CLI tool
    """
    if sys.version_info[0] < 3:
        print("Must be using Python 3! Exiting ...")
        exit(-1)

    print("Running " + version_string + "\n")

    usage = "\n%prog -i inputfile\n"

    parser = OptionParser(usage=usage)
    parser.add_option("-i", dest="inputfile",
                      action="store", type="string",
                      help="/logs/SystemVersion/SystemVersion.plist To Be Searched")
    (options, args) = parser.parse_args()

    if options.inputfile:
        pl = getProductInfo(options.inputfile)
        print("ProductName = %s" % pl["ProductName"])
        print("ProductVersion = %s" % pl["ProductVersion"])
        print("ProductBuildVersion = %s" % pl["ProductBuildVersion"])
    else:
        print("WARNING -i option is mandatory!")


# --------------------------------------------------------------------------- #

"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()


# That's all folk ;)
