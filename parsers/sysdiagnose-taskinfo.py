#! /usr/bin/env python3

# For Python3
# Script to parse taskinfo.txt to ease parsing
# Author: david@autopsit.org
#
# TODO define output
# - search this artifact to extract more
#
import re
import sys
import json
from optparse import OptionParser

version_string = "sysdiagnose-taskinfo.py v2020-02-07 Version 1.0"

#----- definition for parsing.py script -----#
#-----         DO NET DELETE             ----#

parser_description = "Parsing taskinfo txt file"
parser_input = "taskinfo"
parser_call = "get_num_tasks"

#--------------------------------------------#


# --------------------------------------------------------------------------- #
def get_num_tasks(filename, ios_version=13):
    """
        Return -1 if parsing failed
    """
    num_tasks = -1
    try:
        fd = open(filename, "r")
        for line in fd:
            result = re.search(r'(num tasks: )(\d+)', line)
            if(result is not None):
                num_tasks = int(result.group(2))
                break
        fd.close()

    except Exception as e:
        print("Impossible to parse taskinfo.txt: %s" % str(e))
    return num_tasks

def get_tasks(filename, ios_version=13):
    numb_tasks = get_num_tasks(filename, ios_version)
    # TODO add other parsing but requires a non empty task list ^^
    return { "numb_tasks" : numb_tasks, "tasks" : []}

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
                      help="taskinfo.txt")
    (options, args) = parser.parse_args()

    #no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        exit(-1)

    # parse PS file :)
    if options.inputfile:
        print("Number of tasks on device: %d" % get_num_tasks(options.inputfile))
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
