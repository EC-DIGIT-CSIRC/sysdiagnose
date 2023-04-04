#! /usr/bin/env python3

# For Python3
# Script to extract timestamp and generate a timesketch output
# Author: david@autopsit.org

import os
import sys
import json
import datetime
from optparse import OptionParser

# Structure:
# filename : parsing_function
timestamps_files = {
    "sysdiagnose-mobileactivation.json" : "__extract_ts_mobileactivation",
    "sysdiagnose-powerlogs.json" : {},
}


# Timesketch format:
# {"message": "A message","timestamp": 123456789,"datetime": "2015-07-24T19:01:01+00:00","timestamp_desc": "Write time","extra_field_1": "foo"}
timeline = []

def __extract_ts_mobileaction(filename):
    try:
        with open(filename, 'r') as fd:
            data = json.load(fd)
            if "events" in data.keys():
                for event in data["events"]:
                    timestamp = datetime.strptime(event["timestamp"], "%Y-%m-%d %H:%M:%S")
                    ts_event = {
                        "message": "Mobile Activation",
                        "timestamp" : timestamp.timestamp(),
                        "datetime" : timestamp.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                        "timestamp_desc" : "Mobile Activation Time",
                        "extra_field_1" : "Build Version: %s" % event["build_version"]
                    }
                    timeline.append(ts_event)
            else:
                return False
        return True
    except Exception as e:
        print("ERROR while extracting timestamp from %s" %  filename)
        print(e)
        return False
    return False

def parse_json(jsondir):
    """
        Call all the functions defined to extract timestamp from various artifacts
        Return a JSON file compatible with TimeSketch
    """

    # Loop through all the files to check
    for parser in timestamps_files.keys():
        if os.path.exists(parser):
            parser_function = globals()[timestamps_files[parser]]
            parser_function(parser)

    # return the timeline as JSON
    return json.dump(timeline)

# --------------------------------------------------------------------------- #
"""
    Main function
"""
def main():

    if sys.version_info[0] < 3:
        print("Must be using Python 3! Exiting ...")
        exit(-1)

    print("Running " + version_string + "\n")

    usage = "\n%prog -d JSON directory\n"

    parser = OptionParser(usage=usage)
    parser.add_option("-d", dest="inputdir",
                      action="store", type="string",
                      help="Directory containing JSON from parsers")
    (options, args) = parser.parse_args()

    #no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        exit(-1)

    # parse PS file :)
    if options.inputdir:
        timeline = parse_json(options.inputdir)
        print(timeline)
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