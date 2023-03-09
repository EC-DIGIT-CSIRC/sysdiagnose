#! /usr/bin/env python3

# For Python3
# Script to parse system_logs.logarchive
# Author: david@autopsit.org
#
#
# TODO: fix print bug in main by adding an argument that output > stdout to get_logs
import os
import sys
import json
import shutil
import platform
from optparse import OptionParser

version_string = "sysdiagnose-logarchive.py v2020-02-07 Version 1.0"

#----- definition for parsing.py script -----#
#-----         DO NET DELETE             ----#

parser_description = "Parsing system_logs.logarchive folder"
parser_input = "logarchive_folder"
parser_call = "get_logs"

#--------------------------------------------#

cmd_parsing_osx = "/usr/bin/log show %s --style json" # fastest and short version
#cmd_parsing_osx = "/usr/bin/log show %s --info --style json" # to enable debug, add --debug
#cmd_parsing_osx = "/usr/bin/log show %s --info --debug --style json"

# Linux parsing relies on UnifiedLogReader: 
#       https://github.com/ydkhatri/UnifiedLogReader
cmd_parsing_linux = "/usr/bin/python3 /home/david/.local/bin/UnifiedLogReader.py -l INFO -f SQLITE %s %s/timesync/ %s %s" # 3x the same path, last = output
#   -f FORMAT, --output_format FORMAT
#                        Output format: SQLITE, TSV_ALL, LOG_DEFAULT  (Default is LOG_DEFAULT)
#  -l LOG_LEVEL, --log_level LOG_LEVEL
#                        Log levels: INFO, DEBUG, WARNING, ERROR (Default is INFO)

# --------------------------------------------------------------------------- #
def get_logs(filename, ios_version=13, output=sys.stdout):
    """
        Parse the system_logs.logarchive.  When running on OS X, use native tools.
        On other system use a 3rd party library.
    """
    if(platform.system() == "Darwin"):
        return get_logs_on_osx(filename, output) 
    else:
        outpath = "../tmp.data/"
        __cleanup(outpath)
        os.makedirs(outpath)
        if(get_logs_on_linux(filename, outpath)):
            normalize_unified_logs("%s/unifiedlogs.sqlite" % output)
        __cleanup(outpath)
    return None


def __cleanup(outpath):
    if(os.path.exists(outpath)):
        shutil.rmtree(outpath, ignore_errors=True)
    return


def get_logs_on_osx(filename, output):
    cmd_line = cmd_parsing_osx % (filename)
    return __execute_cmd_and_get_result(cmd_line,  filename)


def get_logs_on_linux(filename, output):
    cmd_line = cmd_parsing_linux % (filename, filename, filename, output)
    return __execute_cmd_and_get_result(cmd_line, filename)
    

def normalize_unified_logs(filename="./unifiedlogs.sqlite", output=sys.stdout):
    """
    Parse the SQLite produced by UnifiedLogs to get a JSON file.
    This required to get a SQLITE output from UnifiedLogs
    """
    sys.path.append(os.path.abspath('../'))
    from utils import times
    from utils import sqlite2json

    unifiedlogs = sqlite2json.sqlite2struct(filename)
    try:
        outfd = output
        if(output is not sys.stdout):
           outfd = open(output, "w")
        outfd.write(sqlite2json.dump2json(unifiedlogs))
        if(outfd is not sys.stdout):
            outfd.close()
    except Exception as e:
        print("Impossible to convert %s to JSON (%s)" % (filename, str(e)))
    return


def __execute_cmd_and_get_result(command, filename, outfile=sys.stdout):
    import subprocess
    try:
        cmd_array = command.split()
        process = subprocess.Popen(cmd_array, stdout=subprocess.PIPE, universal_newlines=True)
        resulttxt = ""
        outfd = outfile
        if(outfile is not sys.stdout): # handle case were not printing to stdout
            outfd = open(outfile, "w")
        while True:
            if(process.poll() is None):
                output = process.stdout.readline()
                if(output == ""):
                    break
                else:
                    outfd.write(output)
                    resulttxt += output
            else:
                break
        if(outfd is not sys.stdout):
            outfd.close()
        return True
    except Exception as e:
         print("Impossible to parse %s: %s" % (filename, str(e)))
    return False

# --------------------------------------------------------------------------- #
"""
    Main function
"""
def main():

    if sys.version_info[0] < 3:
        print("Must be using Python 3! Exiting ...")
        exit(-1)

    print("Running " + version_string + "\n")

    usage = "\n%prog -i inputfile\n"

    parser = OptionParser(usage=usage)
    parser.add_option("-i", dest="inputfile",
                      action="store", type="string",
                      help="PRovide path to ystem_logs.logarchive folder")
    parser.add_option("-j", dest="unifiedlog",
                      action="store", type="string",
                      help="Proceed with a second pass on the result of UnifiedLogs to produce a JSON file (path to logs.txt file)")
    (options, args) = parser.parse_args()

    #no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        exit(-1)

    # parse PS file :)
    if options.inputfile:
        get_logs(options.inputfile)
    elif options.unifiedlog:
        normalize_unified_logs(options.unifiedlog)
    else:
        print("WARNING -i or -j option is mandatory!")

# --------------------------------------------------------------------------- #

"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()


# That's all folk ;)
