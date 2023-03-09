#! /usr/bin/env python3

# For Python3
# Script to parse ps.txt to ease parsing
# Author: david@autopsit.org
#
# TODO define output
# - json
# - tree structure
# - simplified
#
import re
import sys
import json
from optparse import OptionParser

version_string = "sysdiagnose-ps.py v2019-10-14 Version 1.0"

#----- definition for parsing.py script -----#
#-----         DO NET DELETE             ----#

parser_description = "Parsing ps.txt file"
parser_input = "ps"
parser_call = "parse_ps"

#--------------------------------------------#

# --------------------------------------------------------------------------- #
def parse_ps(filename, ios_version=13):
  processes = {}
  try:

        fd = open(filename, "r")
        fd.readline() # skip header line

        for line in fd:
            """
            USER             UID   PID  PPID  %CPU %MEM PRI NI      VSZ    RSS WCHAN    TT  STAT STARTED      TIME COMMAND
            root               0     1     0   0.0  0.4  37  0  4226848   8912 -        ??  Ss   14Jan19   7:27.40 /sbin/launchd
            """
            patterns = re.split("\s+", line)
            # key of hash table is PID
            processes[int(patterns[2])] = { "USER"    :  patterns[0],
                                       "UID"     :  patterns[1],
                                       "PID"     :  int(patterns[2]),
                                       "PPID"    :  int(patterns[3]),
                                       "CPU"     :  patterns[4],
                                       "MEM"     :  patterns[5],
                                       "PRI"     :  patterns[6],
                                       "NI"      :  patterns[7],
                                       "VSZ"     :  patterns[8],
                                       "RSS"     :  patterns[9],
                                       "WCHAN"   :  patterns[10],
                                       "TT"      :  patterns[11],
                                       "STAT"    :  patterns[12],
                                       "STARTED" :  patterns[13],
                                       "TIME"    :  patterns[14],
                                       "COMMAND" :  patterns[15] }
        fd.close()
  except Exception as e:
    print("Impossible to parse ps.txt: %s" % str(e))
  return processes


"""
    Export the process structure to a json file
"""
def export_to_json(processes, filename="./ps.json"):
        json_ps = json.dumps(processes, indent=4)
        try:
            fd = open(filename, "w")
            fd.write(json_ps)
            fd.close()
        except:
            print("Impossible to dump the processes to %s\n" % filename)

"""
    Tree export to stdout like volatility pstree plugin
"""
def export_as_tree(processes, with_graph=False):
    ppid = {}
    for pid in processes.keys():
        if not processes[pid]["PPID"] in ppid.keys(): # not an already a known PPID
            ppid[processes[pid]["PPID"]] = [] # create an empty array
        ppid[processes[pid]["PPID"]].append(processes[pid])

    # generate first the dot if requested
    if(with_graph):
      generate_graph(processes)

    # print tree
    ppid = _print_tree(ppid, 0, 0)
    for pid in ppid.keys():
      ppid = _print_tree(ppid, pid, 0) # print orphan processes
    return

def _print_tree(ppid, node=0, depth=0):
    # check that node is in ppid list
    if node not in ppid.keys():
      return ppid

    # loop on all the child of node
    for process in ppid[node]:
      print(depth*"    " + "%s (PID: %d, PPID: %d, USER: %s)" % (process["COMMAND"], process["PID"], process["PPID"], process["USER"]))
      ppid = _print_tree(ppid, process["PID"], depth+1) # recurse on childs of current process
    del ppid[node] # remove the current child from process

    # return
    return ppid


def generate_graph(processes):
  from graphviz import Digraph
  dot = Digraph(comment="Process tree")

  # generate all nodes
  for pid in processes.keys():
    dot.node(str(pid), processes[pid]["COMMAND"])

  # add links
  for pid in processes.keys():
    dot.edge(str(processes[pid]["PPID"]), str(pid), constraint='false')

  # save and create graph
  dot.render("./ps.gv", view=True)

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
                      help="ps.txt")
    (options, args) = parser.parse_args()

    #no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        exit(-1)

    # parse PS file :)
    if options.inputfile:
        processes = parse_ps(options.inputfile)
        export_as_tree(processes, True)
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
