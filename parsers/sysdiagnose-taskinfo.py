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
parser_call = "get_tasks"

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

def parse_task_block(fd, current_threat_id, ios_version=13):
    """
        Receive a pointer to the start of task file and parse it.
        Return a hash table as a result.

        Structure:
        ----------
        thread ID: 0xf2e6f / 994927
        user/system time: 0.000466 s / 0.000000 s
        CPU usage (over last tick): 0%
        sched mode: timeshare
        policy: POLICY_TIMESHARE
                timeshare max  priority: 63
                timeshare base priority: 20
                timeshare cur  priority: 20
                timeshare depressed: NO, prio -1
        requested policy:
                req thread qos: THREAD_QOS_UTILITY, relprio: 0
                req workqueue/pthread overrides:
                        req legacy qos override: THREAD_QOS_UNSPECIFIED
                        req workqueue qos override: THREAD_QOS_UNSPECIFIED
                req kernel overrides:
                        req kevent overrides: THREAD_QOS_UNSPECIFIED
                        req workloop servicer override: THREAD_QOS_UNSPECIFIED
                req turnstiles sync promotion qos: THREAD_QOS_UNSPECIFIED, user promotion base pri: 0
                req latency qos: LATENCY_QOS_TIER_UNSPECIFIED
                req thruput qos: THROUGHPUT_QOS_TIER_UNSPECIFIED
                req darwin BG: NO
                req internal/external iotier: THROTTLE_LEVEL_TIER0 (IMPORTANT) / THROTTLE_LEVEL_TIER0 (IMPORTANT)
                req other:
        effective policy:
                eff thread qos: THREAD_QOS_UTILITY
                eff thread qos relprio: 0
                eff promotion qos: THREAD_QOS_UTILITY
                eff latency qos: LATENCY_QOS_TIER_3
                eff thruput qos: THROUGHPUT_QOS_TIER_2
                eff darwin BG: NO
                eff iotier: THROTTLE_LEVEL_TIER1 (STANDARD)
                eff other: ui-is-urgent (47)
        run state: TH_STATE_WAITING
        flags: TH_FLAGS_SWAPPED |  |
        suspend count: 0
        sleep time: 0 s
        importance in task: 0

    """
    result = {}
    result["policy"] = {}
    result["requested policy"] = {}
    result["effective policy"] = {}
    
    for line in fd:
        line = line.strip()
    
        # break if end of task block
        if len(line) == 0: 
            return result
        
        # global info on task
        elif line.startswith('user/system time:'):
            result["user time"] = line.split()[3]
            result["system time"] = line.split()[5]
        elif line.startswith('CPU usage (over last tick):'):
            result["CPU usage"] = line.split()[5][:-1]
        elif line.startswith('sched mode:'):
            result["sched mode"] = line.split()[2]
        
        # Policy
        elif line.startswith('policy:'):
            continue
        #                 timeshare max  priority: 63
        #       timeshare base priority: 20
        #        timeshare cur  priority: 20
        #        timeshare depressed: NO, prio -1
        #elif line.startswith(''):
        #    continue

        # Requested Policy
        elif line.startswith("requested policy:"):
            continue
        elif line.startswith('req thread qos:'):
            result["requested policy"]["req thread qos"] = line.split()[3][:-1]
        elif line.startswith('req legacy qos override:'):
            result["requested policy"]["req legacy qos override"] = line.split()[4][:-1]
        elif line.startswith('req workqueue qos override:'):
            result["requested policy"]["req workqueue qos override"] = line.split()[4][:-1]
        elif line.startswith('req kevent overrides:'):
            result["requested policy"]["req kevent overrides"] = line.split()[3][:-1]
        elif line.startswith('req workloop servicer override:'):
            result["requested policy"]["req workloop servicer override"] = line.split()[4][:-1]
        elif line.startswith('req turnstiles sync promotion qos:'):
            result["requested policy"]["req turnstiles sync promotion qos"] = line.split()[5][:-1]
        elif line.startswith('req latency qos:'):
            result["requested policy"]["req latency qos"] = line.split()[3][:-1]
        elif line.startswith('req thruput qos:'):
            result["requested policy"]["req thruput qos"] = line.split()[3][:-1]
        elif line.startswith('req darwin BG:'):
            result["requested policy"]["req darwin bg"] = line.split()[3]
        elif line.startswith('req internal/external iotier:'):
            result["requested policy"]["req internal iotier"] = line.split()[3]
            result["requested policy"]["req external iotier"] = line.split()[5]
        
        # Effective Policy Part
        elif line.startswith("effective policy:"):
             continue
        elif line.startswith('eff thread qos:'):
            result["effective policy"]["eff thread qos"] = line.split()[3]
        elif line.startswith('eff thread qos relprio:'):
            result["effective policy"]["eff thread qos relprio"] = line.split()[4]
        elif line.startswith('eff promotion qos:'):
            result["effective policy"]["eff promotion qos"] = line.split()[3]
        elif line.startswith('eff latency qos:'):
            result["effective policy"]["eff latency qos"] = line.split()[3]
        elif line.startswith('eff thruput qos:'):
            result["effective policy"]["eff thruput qos"] = line.split()[3]
        elif line.startswith('eff darwin BG:'):
            result["effective policy"]["eff darwin bg"] = line.split()[3]

        # Handline unknown
        else:
            continue # unknown line
            print("WARNING: Unexpected line detected: %s " % line)
        #Missing 
        #run state: TH_STATE_WAITING
        #flags: TH_FLAGS_SWAPPED |  |
        #suspend count: 0
        #sleep time: 0 s
        #importance in task: 0
    return result


def search_task_block(fd, ios_version):
    result = {}
    try:
        for line in fd:
            line = line.strip()
            if line.startswith('thread ID:'):
                current_threatID = line.split()[2]
                print("Parsing ThreatId: %s" % current_threatID)
                result[current_threatID] = parse_task_block(fd, current_threatID, ios_version)
            else:
                continue

    except Exception as e:
        print("An unknown error occurs while searching for task block")
        print(e)

    return result

"""
    Parse all elements
"""
def get_tasks(filename, ios_version=13):
    numb_tasks = get_num_tasks(filename, ios_version)
    tasks = {}

    try:
        fd = open(filename, "r")
        for line in fd:
            line = line.strip()
            # search for the right place in text file
            if(line.startswith("threads:")):
                tasks = search_task_block(fd, ios_version)
            else:
                continue
        fd.close()
    except Exception as e:
        print("Impossible to open %s" % filename)
        print(e)
    
    return { "numb_tasks" : numb_tasks, "tasks" : tasks}

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
