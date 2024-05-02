#! /usr/bin/env python3

# For Python3
# Script to print connection info from logs/appinstallation/AppUpdates.sqlite.db (iOS12)
# New version of iOS store data into logs/appinstallation/appstored.sqlitedb
# Author: david@autopsit.org

# PID: encoded in Litlle Endian??
# TODO - add support of iOS13...


from optparse import OptionParser
from utils import sqlite2json
import datetime
import glob
import json
import os
import sqlite3
import sys

version_string = "sysdiagnose-appinstallation.py v2019-11-22 Version 2.0"

# ----- definition for parsing.py script -----#

parser_description = "Parsing app installation logs"
parser_input = "appinstallation"
parser_call = "get_appinstallation"

# --------------------------------------------#

# --------------------------------------------------------------------------- #


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'logs/appinstallation/AppUpdates.sqlitedb',
        'logs/appinstallation/appstored.sqlitedb'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def get_appinstallation(dbpath, ios_version=13):
    # FIXME result can contain data in binary form. Apply the misc.json_serializable function to convert it to clean JSON.
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
            print(f"{pid},{bundle_id},{utctime}")
    except Exception as e:
        print(f"AN UNHANDLED ERROR OCCURED AND THE DB WAS NOT PARSED. Reason: {str(e)}")


def get_appinstallation_ios13(dbpath):
    appinstallation = sqlite2json.sqlite2struct(dbpath)
    return json.loads(sqlite2json.dump2json(appinstallation))


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
                      help="logs/appinstallation/AppUpdates.sqlite.db to be parsed")
    (options, args) = parser.parse_args()

    # no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(-1)

    get_appinstallation(options.inputfile)

# --------------------------------------------------------------------------- #


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()

# That's all folk ;)
