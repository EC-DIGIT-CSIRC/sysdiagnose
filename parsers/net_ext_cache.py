#! /usr/bin/env python3

# For Python3
# Script to print the values from logs/Networking/com.apple.networkextension.cache.plist
# Author: cheeky4n6monkey@gmail.com
#
# Change log: David DURVAUX - add function are more granular approach

import sys
from optparse import OptionParser
import plistlib


version_string = "sysdiagnose-net-ext-cache.py v2019-05-10 Version 2.0"

# --------------------------------------------------------------------------- #


def getNetExtCache(filename, ios_version=13):
    result = []
    try:
        with open(filename, 'rb') as fp:
            pl = plistlib.load(fp)

            if 'app-rules' in pl.keys():
                for key, list1 in pl["app-rules"].items():
                    result.append([str(key), list1])
    except Exception as e:
        print(f"Impossible to parse {filename}. Reason: {str(e)}")
    return result


# --------------------------------------------------------------------------- #

def main():

    usage = "\n%prog -i inputfile\n"

    parser = OptionParser(usage=usage)
    parser.add_option("-i", dest="inputfile",
                      action="store", type="string",
                      help="logs/Networking/com.apple.networkextension.cache.plist To Be Searched")
    parser.add_option("-v", dest="verbose",
                      action="store_true", default=False,
                      help="Print GUIDs as well as app names")
    (options, args) = parser.parse_args()

    # no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(-1)

    print(f"Running {version_string}\n")

    result = getNetExtCache(options.inputfile)
    count = 0
    for line in result:
        count += 1
        [key, list1] = line
        if (options.verbose):
            print(str(key) + " = " + ', '.join(list1))   # verbose with GUIDs
        else:
            print(str(key))   # just app names

    print(f"\n {str(count)} cache entries retrieved\n")


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()


# That's all folk ;)
