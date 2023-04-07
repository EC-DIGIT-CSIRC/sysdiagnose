#! /usr/bin/env python3

# For Python3
# Script to extract timestamp and generate a timesketch output
# Author: david@autopsit.org

import os
import sys
import json
from datetime import datetime
from optparse import OptionParser

version_string = "sysdiagnose-timeliner.py v2023-04-05 Version 0.1"

# Structure:
# filename : parsing_function
timestamps_files = {
#    "sysdiagnose-accessibility-tcc.json" : "__extract_ts_accessibility_tcc",
    #   appinstallation: TODO
    #   itunesstore: TODO
#    "sysdiagnose-mobileactivation.json" : "__extract_ts_mobileactivation",
#    "sysdiagnose-powerlogs.json" : "__extract_ts_powerlogs", #TO DEBUG!!
    # psthread: TODO
#    "sysdiagnose-swcutil.json" : "__extract_ts_swcutil",
    "sysdiagnose-logarchive.json" : "__extract_ts_logarchive",
}


# Timesketch format:
# {"message": "A message","timestamp": 123456789,"datetime": "2015-07-24T19:01:01+00:00","timestamp_desc": "Write time","extra_field_1": "foo"}
timeline = []

def __extract_ts_mobileactivation(filename):
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

def __extract_ts_powerlogs(filename):
    try:
        with open(filename, 'r') as fd:
            data = json.load(fd)
            print("ERROR: not implemented!!")
            # -- IMPLEMENT HERE --
        return True
    except Exception as e:
        print("ERROR while extracting timestamp from %s" %  filename)
        print(e)
        return False
    return False

def __extract_ts_swcutil(filename):
    """
        FORMAT:
            "Service": "applinks",
            "App ID": "CYSVS85Q6G.be.fgov.ehealth.DGC",
            "App Version": "193.0",
            "App PI": "<LSPersistentIdentifier 0xdac8132d0> { v = 0, t = 0x8, u = 0x3ec, db = 2135AC5C-110D-4E2E-A350-90494244DBB4, {length = 8, bytes = 0xec03000000000000} }",
            "Domain": "int.cert-app.be",
            "User Approval": "unspecified",
            "Site/Fmwk Approval": "denied",
            "Flags": "",
            "Last Checked": "2023-02-23 23:00:15 +0000",
            "Next Check": "2023-02-28 22:06:35 +0000"
        },
    """
    try:
        with open(filename, 'r') as fd:
            data = json.load(fd)
            if "db" in data.keys():
                for service in data["db"]:
                    timestamp = datetime.strptime(service["Last Checked"], "%Y-%m-%d %H:%M:%S %z")
                    ts_event = {
                        "message": service["Service"],
                        "timestamp" : timestamp.timestamp(),
                        "datetime" : timestamp.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                        "timestamp_desc" : "swcutil last checkeed",
                        "extra_field_1" : "application: %s" % service["App ID"]
                    }
                    timeline.append(ts_event) 
        return True
    except Exception as e:
        print("ERROR while extracting timestamp from %s" %  filename)
        print(e)
        return False
    return False


def __extract_ts_accessibility_tcc(filename):
    """
        Service format
            { "service": "kTCCServiceCamera" },
            { "client": "eu.europa.publications.ECASMobile" },
            { "client_type": "0" },
            { "auth_value": "2" },
            { "auth_reason": "0" },
            { "auth_version": "1" },
            { "csreq": "None" },
            { "policy_id": "None" },
            { "indirect_object_identifier_type": "None" },
            { "indirect_object_identifier": "UNUSED" },
            { "indirect_object_code_identity": "None" },
            { "flags": "None" },
            { "last_modified": "1537694318" }
    """
    try:
        with open(filename, 'r') as fd:
            data = json.load(fd)
            if "access" in data.keys():
                for access in data["access"]:
                     # convert to hashtable
                    service = {}
                    for line in access:
                        keys = line.keys()
                        for key in keys:
                            service[key] = line[key]

                    # create timeline entry
                    timestamp = datetime.fromtimestamp(int(service["last_modified"]))
                    ts_event = {
                        "message": service["service"],
                        "timestamp" : timestamp.timestamp(),
                        "datetime" : timestamp.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                        "timestamp_desc" : "Accessibility TC Last Modified",
                        "extra_field_1" : "client: %s" % service["client"]
                    }
                    timeline.append(ts_event) 
        return True
    except Exception as e:
        print("ERROR while extracting timestamp from %s" %  filename)
        print(e)
        return False
    return False


def __extract_ts_logarchive(filename):
    """
        Entry format:
        {
            "traceID" : 4928246544425287684,
            "eventMessage" : "EAP: eapState=2",
            "eventType" : "logEvent",
            "source" : null,
            "formatString" : "%{public}@",
            "activityIdentifier" : 0,
            "subsystem" : "com.apple.WiFiPolicy",
            "category" : "",
            "threadID" : 500795,
            "senderImageUUID" : "452AEEAF-04BA-3FCA-83C8-16F162D87321",
            "backtrace" : {
                "frames" : [
                {
                    "imageOffset" : 28940,
                    "imageUUID" : "452AEEAF-04BA-3FCA-83C8-16F162D87321"
                }
            ]
            },
            "bootUUID" : "2DF74FE0-4876-43B0-828B-F285FA4D42F5",
            "processImagePath" : "\/usr\/sbin\/wifid",
            "timestamp" : "2023-02-23 10:44:02.761747+0100",
            "senderImagePath" : "\/System\/Library\/PrivateFrameworks\/WiFiPolicy.framework\/WiFiPolicy",
            "machTimestamp" : 3208860279380,
            "messageType" : "Default",
            "processImageUUID" : "F972AB5A-6713-3F33-8675-E87C631497F6",
            "processID" : 50,
            "senderProgramCounter" : 28940,
            "parentActivityIdentifier" : 0,
            "timezoneName" : ""
        },
    """
    try:
        with open(filename, 'r') as fd:
            data = json.load(fd)

            try:
                for trace in data:
                    # create timeline entry
                    timestamp = datetime.strptime(trace["timestamp"], "%Y-%m-%d %H:%M:%S.%f%z")
                    ts_event = {
                        "message": trace["eventMessage"],
                        "timestamp" : timestamp.timestamp(),
                        "datetime" : timestamp.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                        "timestamp_desc" : "Entry in logarchive: %s" % trace["eventType"],
                        "extra_field_1" : "subsystem: %s; processImageUUID: %s; processImagePath: %s" % (trace["subsystem"], trace["processImageUUID"], trace["processImagePath"])
                    }
                    timeline.append(ts_event)
            except Exception as e:
                print("WARNING: trace not parsed: %s" %  trace) 
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
        path = "%s/%s" % (jsondir, parser)

        if os.path.exists(path):
            function_name = timestamps_files[parser]
            parser_function = globals()[function_name]
            parser_function(path)

    # return the timeline as JSON
    return timeline

def save_timeline(timeline, ts_file):
    try:
        with open(ts_file, 'w') as f:
            json.dump(timeline, f)
    except Exception as e:
        print("ERROR: impossible to save timeline to %s" % timeline)

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
    parser.add_option("-o", dest="outputfile",
                      action="store", type="string",
                      help="JSON tile to save the timeline")
    (options, args) = parser.parse_args()

    #no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        exit(-1)

    # parse PS file :)
    if options.inputdir:
        timeline = parse_json(options.inputdir)
        if options.outputfile:
            save_timeline(timeline, options.outputfile)
        else:
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