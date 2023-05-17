#! /usr/bin/env python3

# For Python3
# Script to parse the swcutil_show.txt file
# Author: Emilien Le Jamtel

"""sysdiagnose intialize.

Usage:
  sysdiagnose-spindumpnosymbols.py -i <file>
  sysdiagnose-spindumpnosymbols.py (-h | --help)
  sysdiagnose-spindumpnosymbols.py --version

Options:
  -h --help     Show this screen.
  -v --version     Show version.
"""

import sys
from optparse import OptionParser
import plistlib
import json
from docopt import docopt
from tabulate import tabulate
import re
import pprint

# ----- definition for parsing.py script -----#
# -----         DO NOT DELETE             ----#

parser_description = "Parsing spindump-nosymbols file"
parser_input = "spindump-nosymbols"
parser_call = "parsespindumpNS"

# --------------------------------------------#


def parsespindumpNS(file):
    with open(file, 'r') as f_in:
        # init section
        headers = []
        processes_raw = []
        status = 'headers'

        # stripping
        for line in f_in:
            if line.strip() == "" or line.strip() == "Heavy format: stacks are sorted by count" or line.strip() == "Use -i and -timeline to re-report with chronological sorting":
                continue
            elif line.strip() == "------------------------------------------------------------":
                status = 'processes_raw'
                continue
            elif line.strip() == "Spindump binary format":
                status = 'binary'
                continue
            elif status == 'headers':
                headers.append(line.strip())
                continue
            elif status == 'processes_raw':
                processes_raw.append(line.strip())
                continue

        # call parsing function per section
        output = parse_basic(headers)
        output['processes'] = parse_processes(processes_raw)

    return output


def parse_basic(data):
    output = {}
    for line in data:
        splitted = line.split(":", 1)
        if len(splitted) > 1:
            output[splitted[0]] = splitted[1].strip()
    return output


def parse_processes(data):
    # init
    processes = []
    init = True
    process = []
    for line in data:
        if "Process:" in line.strip():
            if not init:
                processes.append(parse_process(process))
                process = [line.strip()]
            else:
                init = False
                process.append(line.strip())
        else:
            process.append(line.strip())
    processes.append(parse_process(process))
    return processes


def parse_process(data):
    # init
    status = 'infos'
    infos = []
    threads = []
    images = []
    for line in data:
        if "Thread 0x" in line.strip():
            status = "threads"
            threads.append(line.strip())
            continue
        elif "Binary Images:" in line.strip():
            status = "images"
            continue
        elif status == "infos":
            infos.append(line.strip())
            continue
        elif status == "threads":
            threads.append(line.strip())
            continue
        elif status == "images":
            images.append(line.strip())
            continue
    process = parse_basic(infos)
    process['threads'] = parse_threads(threads)
    process['images'] = parse_images(images)

    return process


def parse_threads(data):
    # init
    init = True
    threads = []
    thread = []
    for line in data:
        if "Thread 0x" in line.strip():
            if not init:
                threads.append(parse_thread(thread))
                thread = [line.strip()]
            else:
                init = False
                thread.append(line.strip())
        else:
            thread.append(line.strip())
    threads.append(parse_thread(thread))
    return threads


def parse_thread(data):
    output = {}
    # parse first line
    # Thread Hex value
    threadHEXregex = re.search(r"Thread 0x..", data[0])
    output['thread'] = threadHEXregex.group(0).split(" ", 1)[1]
    # Thread Name / DispatchQueue
    if "DispatchQueue \"" in data[0]:
        dispacthregex = re.search(r"DispatchQueue(.*)\"\(", data[0])
        output['DispatchQueue'] = dispacthregex.group(0).split("\"")[1]
    if "Thread name \"" in data[0]:
        dispacthregex = re.search(r"Thread name\ \"(.*)\"", data[0])
        output['ThreadName'] = dispacthregex.group(0).split("\"")[1]
    # priority
    if "priority" in data[0]:
        priorityregex = re.search(r"priority\ [0-9]+", data[0])
        output['priority'] = priorityregex.group(0).split(" ", 1)[1]
    if "cpu time" in data[0]:
        cputimeregex = re.search(r"cpu\ time\ (.*)\)", data[0])
        output["cputime"] = cputimeregex.group(0).split("time ", 1)[1]

    output["loaded"] = []

    for line in data[1:]:
        loaded={}
        if "+" in line:
            loaded["library"] = line.split("(", 1)[1].split("+", 1)[0].strip()
            loaded["int"] = line.split("(", 1)[1].split("+", 1)[1].split(")", 1)[0].strip()
            loaded["hex"] = line.split("[", 1)[1][:-1].strip()
        elif "truncated backtrace>" not in line:
            loaded["hex"] = line.split("[", 1)[1][:-1].strip()
        output["loaded"].append(loaded)
    return output


def parse_images(data):
    images=[]
    for line in data:
        image = {}
        if line.strip() is not None:
            clean = ' '.join(line.split(" ")).split()
            image['start'] = clean[0]
            image['end'] = clean[2]
            image['image'] = clean[3]
            image['UUID'] = clean[4][1:-1]
            try:
                image['path'] = clean[5]
            except:     # noqa E722
                pass
            images.append(image)
    return images


def main():
    """
        Main function, to be called when used as CLI tool
    """

    arguments = docopt(__doc__, version='parser for networkextension.plist v0.1')

    ### test
    if arguments['-i']:
        # Output is good enough, just print
        print(json.dumps(parsespindumpNS(arguments['<file>']), indent=4))
        sys.exit()
    ### test

    return 0


# --------------------------------------------------------------------------- #

"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()


# That's all folk ;)
