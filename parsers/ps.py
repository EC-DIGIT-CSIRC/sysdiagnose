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
import sys
import json
from optparse import OptionParser
import glob
import os
import re

parser_description = "Parsing ps.txt file"


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'ps.txt'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    try:
        return parse_ps(get_log_files(path)[0])
    except IndexError:
        return {'error': 'No ps.txt file present'}


def parse_ps(filename):
    result = []
    try:
        with open(filename, "r") as f:
            header = re.split(r"\s+", f.readline().strip())
            header_length = len(header)

            print(f"Found header: {header}")
            for line in f:
                patterns = re.split(r"\s+", line.strip())
                row = {}
                # merge last entries together, as last entry may contain spaces
                for col in range(header_length):
                    # try to cast as int, float and fallback to string
                    col_name = header[col]
                    try:
                        row[col_name] = int(patterns[col])
                        continue
                    except ValueError:
                        try:
                            row[col_name] = float(patterns[col])
                        except ValueError:
                            row[col_name] = patterns[col]
                row[header[-1]] = " ".join(patterns[header_length - 1:])
                result.append(row)
            return result
    except Exception as e:
        print(f"Could not parse ps.txt: {str(e)}")
        return []


"""
    Export the process structure to a json file
"""


def export_to_json(processes, filename="./ps.json"):
    json_ps = json.dumps(processes, indent=4)
    try:
        with open(filename, "w") as fd:
            fd.write(json_ps)
    except Exception as e:
        print(f"Impossible to dump the processes to {filename}. Reason: {str(e)}\n")


"""
    Tree export to stdout like volatility pstree plugin
"""


def export_as_tree(processes, with_graph=False):
    ppid = {}
    for pid in processes.keys():
        if not processes[pid]["PPID"] in ppid.keys():  # not an already a known PPID
            ppid[processes[pid]["PPID"]] = []  # create an empty array
        ppid[processes[pid]["PPID"]].append(processes[pid])

    # generate first the dot if requested
    if (with_graph):
        generate_graph(processes)

    # print tree
    ppid = _print_tree(ppid, 0, 0)
    for pid in ppid.keys():
        ppid = _print_tree(ppid, pid, 0)  # print orphan processes
    return


def _print_tree(ppid, node=0, depth=0):
    # check that node is in ppid list
    if node not in ppid.keys():
        return ppid

    # loop on all the child of node
    for process in ppid[node]:
        print(depth * "    " + "%s (PID: %d, PPID: %d, USER: %s)" %
              (process["COMMAND"], process["PID"], process["PPID"], process["USER"]))
        ppid = _print_tree(ppid, process["PID"], depth + 1)  # recurse on childs of current process
    del ppid[node]  # remove the current child from process

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
    usage = "\n%prog -i inputfile\n"

    parser = OptionParser(usage=usage)
    parser.add_option("-i", dest="inputfile",
                      action="store", type="string",
                      help="ps.txt")
    (options, args) = parser.parse_args()

    # no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(-1)

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
