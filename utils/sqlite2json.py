#! /usr/bin/env python
#
# For Python3
# Script to parse sqlite database and export to JSON (generic)
# Author: david@autopsit.org
#
# iOS13: 4 SQLite DB
#   ./logs/itunesstored/downloads.28.sqlitedb
#   ./logs/powerlogs/powerlog_2019-11-07_17-23_ED7F7E2B.PLSQL
#   ./logs/Accessibility/TCC.db
#   ./logs/appinstallation/appstored.sqlitedb
import sys
import json
import sqlite3
from optparse import OptionParser

version_string = "sqlite2json.py v2020-02-18 Version 1.0"

# --------------------------------------------------------------------------- #


def sqlite2struct(dbpath):
    """
        Transform a SQLite DB to a Python struct.
        If any exception, return None
    """
    try:
        dbstruct = {}
        dbfd = sqlite3.connect(dbpath)
        for table in gettables(dbfd):
            content = table2struct(dbfd, table)
            dbstruct[table] = content
        return dbstruct
    except Exception as e:
        print(f"Could not parse {dbpath}. Reason: {str(e)}", file=sys.stderr)
    return None


def gettables(dbfd):
    tables = []
    cursor = dbfd.cursor()
    for row in cursor.execute("select name from sqlite_master where type = 'table'"):
        [tablename] = row
        tables.append(tablename)
    return tables


def getcolumnsfromtable(dbfd, tablename):
    cursor = dbfd.cursor()
    cursor.execute("SELECT * FROM '%s'" % tablename)
    col_name_list = [tuple[0] for tuple in cursor.description]
    return col_name_list


def table2struct(dbfd, tablename):
    table = []
    column_names = getcolumnsfromtable(dbfd, tablename)
    cursor = dbfd.cursor()
    for row in cursor.execute("SELECT * FROM '%s'" % tablename):
        line = {}
        ptr = 0
        for element in row:
            if not isinstance(element, (str, int, float, bool)):
                element = str(element)
            line[column_names[ptr]] = element
            ptr = ptr + 1
        table.append(line)
    return table


def dump2json(dbstruct, jsonpath="./db.json"):
    jsontxt = json.dumps(dbstruct, indent=4)
    try:
        with open(jsonpath, "w") as fd:
            fd.write(jsontxt)
    except Exception as e:
        print(f"Impossible to dump the UUID to Path to {jsonpath}. Reason: {str(e)}\n", file=sys.stderr)
    return jsontxt

# --------------------------------------------------------------------------- #


def main():
    if sys.version_info[0] < 3:
        print("Must be using Python 3! Exiting ...", file=sys.stderr)
        sys.exit(-1)

    usage = "\n%prog -i inputfile\n"

    parser = OptionParser(usage=usage)
    parser.add_option("-i", dest="inputfile",
                      action="store", type="string",
                      help="SQlite DB To Be Printed")
    (options, args) = parser.parse_args()

    # no arguments given by user, print help and exit
    if options.inputfile:
        print(f"Running {version_string}\n")
        print(sqlite2struct(options.inputfile))
    else:
        parser.print_help()
        sys.exit(-1)
    return


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()

# --------------------------------------------------------------------------- #
# That's all folk ;)
