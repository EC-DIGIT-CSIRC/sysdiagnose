#! /usr/bin/env python3

# For Python3
# Script to print connection info from logs/appinstallation/AppUpdates.sqlite.db (iOS12)
# New version of iOS store data into logs/appinstallation/appstored.sqlitedb
# Author: david@autopsit.org

# PID: encoded in Litlle Endian??
# TODO - add support of iOS13...

import os
import sys
import json
from optparse import OptionParser
import time
import struct
import datetime
import sqlite3

version_string = "sysdiagnose-appinstallation.py v2019-11-22 Version 2.0"

# ----- definition for parsing.py script -----#

parser_description = "Parsing app installation logs"
parser_input = "appinstallation"
parser_call = "get_appinstallation"

# --------------------------------------------#

# --------------------------------------------------------------------------- #


def get_appinstallation(dbpath, ios_version=13):
    if ios_version < 13:
        return print_appinstall_ios12(dbpath)
    else:
        return get_appinstallation_ios13(dbpath)


def print_appinstall_ios12(dbpath):
    try:
        appinstalldb = sqlite3.connect(dbpath)
        cursor = appinstalldb.cursor()
        for row in cursor.execute("SELECT pid, bundle_id, install_date FROM app_updates"):
            [pid, bundle_id, install_date] = row

            # convert install_date from Cocoa EPOCH -> UTC
            epoch = install_date + 978307200  # difference between COCOA and UNIX epoch is 978307200 seconds
            utctime = datetime.datetime.utcfromtimestamp(epoch)

            # convert PID
            # pid =  struct.pack('>I', pid)

            # print result
            print("%s,%s,%s" % (pid, bundle_id, utctime))
    except Exception as e:
        print(f"AN UNHANDLED ERRORS OCCURS AND THE DB WAS NOT PARSED. Reason: {str(e)}")


def get_appinstallation_ios13(dbpath):

    from utils import times
    from utils import sqlite2json

    appinstallation = sqlite2json.sqlite2struct(dbpath)
    return json.loads(sqlite2json.dump2json(appinstallation))


# --------------------------------------------------------------------------- #

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
                      help="logs/appinstallation/AppUpdates.sqlite.db to be parsed")
    (options, args) = parser.parse_args()

    # no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        exit(-1)

    get_appinstallation(options.inputfile)

# --------------------------------------------------------------------------- #


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()

# That's all folk ;)
