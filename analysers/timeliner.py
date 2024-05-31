#! /usr/bin/env python3

# For Python3
# Script to extract timestamp and generate a timesketch output
# Author: david@autopsit.org
#
# Important note: timestamp are in microseconds! standard epoch is in seconds.

import os
import sys
import json
from datetime import datetime
from optparse import OptionParser

version_string = "sysdiagnose-timeliner.py v2023-04-05 Version 0.1"

# ----- definition for analyse.py script -----#
# -----         DO NOT DELETE             ----#

analyser_description = "Generate a Timesketch compatible timeline"
analyser_call = "generate_timeline"
analyser_format = "jsonl"

# Structure:
# filename : parsing_function
timestamps_files = {
    "sysdiagnose-accessibility-tcc.json": "__extract_ts_accessibility_tcc",
    # itunesstore: TODO
    "sysdiagnose-mobileactivation.json": "__extract_ts_mobileactivation",
    "sysdiagnose-powerlogs.json": "__extract_ts_powerlogs",
    "sysdiagnose-swcutil.json": "__extract_ts_swcutil",
    "sysdiagnose-shutdownlogs.json": "__extract_ts_shutdownlogs",
    "sysdiagnose-logarchive.json": "__extract_ts_logarchive",
    "sysdiagnose-wifisecurity.json": "__extract_ts_wifisecurity",
    "sysdiagnose_wifi_known_networks.json": "__extract_ts_wifi_known_networks",
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
                        "timestamp": int(timestamp.timestamp() * 1000000),
                        "datetime": timestamp.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                        "timestamp_desc": "Mobile Activation Time",
                        "extra_field_1": "Build Version: %s" % event["build_version"]
                    }
                    timeline.append(ts_event)
            else:
                return False
        return True
    except Exception as e:
        print(f"ERROR while extracting timestamp from {filename}. Reason: {str(e)}")
        return False
    return False


def __extract_ts_powerlogs(filename):
    try:
        with open(filename, 'r') as fd:
            data = json.load(fd)

            # extract tables of interest
            __extract_ts_powerlogs__PLProcessMonitorAgent_EventPoint_ProcessExit(data)  # PLProcessMonitorAgent_EventPoint_ProcessExit
            __extract_ts_powerlogs__PLProcessMonitorAgent_EventBackward_ProcessExitHistogram(data)  # PLProcessMonitorAgent_EventBackward_ProcessExitHistogram
            __extract_ts_powerlogs__PLAccountingOperator_EventNone_Nodes(data)  # PLAccountingOperator_EventNone_Nodes
        return True
    except Exception as e:
        print(f"ERROR while extracting timestamp from {filename}. Reason: {str(e)}")
        return False
    return False


def __extract_ts_powerlogs__PLProcessMonitorAgent_EventPoint_ProcessExit(jdata):
    proc_exit = jdata["PLProcessMonitorAgent_EventPoint_ProcessExit"]
    for proc in proc_exit:
        timestamp = datetime.fromtimestamp(int(proc["timestamp"]))

        extra_field = ""
        if "IsPermanent" in proc.keys():
            extra_field = "Is permanent: %d" % proc["IsPermanent"]
        ts_event = {
            "message": proc["ProcessName"],
            "timestamp": int(timestamp.timestamp() * 1000000),
            "datetime": timestamp.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "timestamp_desc": "Process Exit with reason code: %d reason namespace %d" % (proc["ReasonCode"], proc["ReasonNamespace"]),
            "extra_field_1": extra_field
        }
        timeline.append(ts_event)
    return


def __extract_ts_powerlogs__PLProcessMonitorAgent_EventBackward_ProcessExitHistogram(jdata):
    events = jdata["PLProcessMonitorAgent_EventBackward_ProcessExitHistogram"]
    for event in events:
        timestamp = datetime.fromtimestamp(int(event["timestamp"]))
        ts_event = {
            "message": event["ProcessName"],
            "timestamp": int(timestamp.timestamp() * 1000000),
            "datetime": timestamp.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "timestamp_desc": "Process Exit with reason code: %d reason namespace %d" % (event["ReasonCode"], event["ReasonNamespace"]),
            "extra_field_1": "Crash frequency: [0-5s]: %d, [5-10s]: %d, [10-60s]: %d, [60s+]: %d" % (event["0s-5s"], event["5s-10s"], event["10s-60s"], event["60s+"])
        }
        timeline.append(ts_event)
    return


def __extract_ts_powerlogs__PLAccountingOperator_EventNone_Nodes(jdata):
    eventnone = jdata["PLAccountingOperator_EventNone_Nodes"]
    for event in eventnone:
        timestamp = datetime.fromtimestamp(int(event["timestamp"]))
        ts_event = {
            "message": event["Name"],
            "timestamp": int(timestamp.timestamp() * 1000000),
            "datetime": timestamp.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "timestamp_desc": "PLAccountingOperator Event",
            "extra_field_1": "Is permanent: %d" % event["IsPermanent"]
        }
        timeline.append(ts_event)
    return

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
    with open(filename, 'r') as fd:
        data = json.load(fd)
        if "db" in data.keys():
            for service in data["db"]:
                try:
                    timestamp = datetime.strptime(service["Last Checked"], "%Y-%m-%d %H:%M:%S %z")
                    ts_event = {
                        "message": service["Service"],
                        "timestamp": int(timestamp.timestamp() * 1000000),
                        "datetime": timestamp.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                        "timestamp_desc": "swcutil last checkeed",
                        "extra_field_1": "application: %s" % service["App ID"]
                    }
                    timeline.append(ts_event)
                except Exception as e:
                    print(f"ERROR {filename} while extracting timestamp from {(service['Service'])} - {(service['App ID'])}. Record not inserted.")
    return True


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
                    # create timeline entry
                    timestamp = datetime.fromtimestamp(int(access["last_modified"]))
                    ts_event = {
                        "message": access["service"],
                        "timestamp": int(timestamp.timestamp() * 1000000),
                        "datetime": timestamp.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                        "timestamp_desc": "Accessibility TC Last Modified",
                        "extra_field_1": "client: %s" % access["client"]
                    }
                    timeline.append(ts_event)
        return True
    except Exception as e:
        print(f"ERROR while extracting timestamp from {filename}. Reason {str(e)}")
        return False
    return False

def __extract_ts_shutdownlogs(filename):
    try:
        with open(filename, 'r') as fd:
            data = json.load(fd)
            for ts in data["data"].keys():
                try:
                    # create timeline entries
                    timestamp = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S+00:00")
                    processes = data["data"][ts]
                    for p in processes:
                        ts_event = {
                            "message": p["path"],
                            "timestamp": int(timestamp.timestamp() * 1000000),
                            "datetime": timestamp.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                            "timestamp_desc": "Entry in shutdown.log",
                            "extra_field_1": "pid: %s" % p["pid"]
                        }
                        timeline.append(ts_event)
                except Exception as e:
                    print(f"WARNING: entry not parsed: {ts}")
        return True
    except Exception as e:
        print(f"ERROR while extracting timestamp from {filename}. Reason: {str(e)}")
        return False
    return False


def __extract_ts_logarchive(filename):
    r"""
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
    """         # XXX FIXME pycodestyle error W605 when not using python's r-strings. Are the backslashes actually there in the data?
    try:
        with open(filename, 'r') as fd:
            data = json.load(fd)
            for trace in data["data"]:
                try:
                    # create timeline entry
                    timestamp = datetime.strptime(trace["timestamp"], "%Y-%m-%d %H:%M:%S.%f%z")
                    ts_event = {
                        "message": trace["eventMessage"],
                        "timestamp": int(timestamp.timestamp() * 1000000),
                        "datetime": timestamp.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                        "timestamp_desc": "Entry in logarchive: %s" % trace["eventType"],
                        "extra_field_1": "subsystem: %s; processImageUUID: %s; processImagePath: %s" % (trace["subsystem"], trace["processImageUUID"], trace["processImagePath"])
                    }
                    timeline.append(ts_event)
                except Exception as e:
                    print(f"WARNING: trace not parsed: {trace}")
        return True
    except Exception as e:
        print(f"ERROR while extracting timestamp from {filename}. Reason: {str(e)}")
        return False
    return False


def __extract_ts_wifisecurity(filename):
    """
        "accc": "<SecAccessControlRef: ck>",
        "acct": "SSID NAME",
        "agrp": "apple",
        "cdat": "2020-09-03 15:44:36 +0000",
        "mdat": "2020-09-03 15:44:36 +0000",
        "musr": "{length = 0, bytes = 0x}",
        "pdmn": "ck",
        "sha1": "{length = 20, bytes = 0x03e144b04a024ddeff9c948ee4d512345679}",
        "svce": "AirPort",
        "sync": "1",
        "tomb": "0"
    """
    try:
        with open(filename, 'r') as fd:
            data = json.load(fd)
            for wifi in data:
                if bool(wifi):
                    # create timeline entry
                    ctimestamp = datetime.strptime(wifi["cdat"], "%Y-%m-%d %H:%M:%S %z")
                    mtimestamp = datetime.strptime(wifi["mdat"], "%Y-%m-%d %H:%M:%S %z")

                    # Event 1: creation
                    ts_event = {
                        "message": wifi["acct"],
                        "timestamp": int(ctimestamp.timestamp() * 1000000),
                        "datetime": ctimestamp.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                        "timestamp_desc": "SSID added to known secured WIFI list",
                        "extra_field_1": wifi["accc"]
                    }
                    timeline.append(ts_event)

                    # Event 2: modification
                    ts_event = {
                        "message": wifi["acct"],
                        "timestamp": int(mtimestamp.timestamp() * 1000000),
                        "datetime": mtimestamp.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                        "timestamp_desc": "SSID modified into the secured WIFI list",
                        "extra_field_1": wifi["accc"]
                    }
                    timeline.append(ts_event)
        return True
    except Exception as e:
        print(f"ERROR while extracting timestamp from {filename}. Reason {str(e)}")
        return False
    return False


def __extract_ts_wifi_known_networks(filename):
    with open(filename, 'r') as fd:
        data = json.load(fd)
        for wifi in data.keys():
            ssid = data[wifi]["SSID"]
            try:
                added = datetime.strptime(data[wifi]["AddedAt"], "%Y-%m-%d %H:%M:%S.%f")

                # WIFI added
                ts_event = {
                    "message": "WIFI %s added" % ssid,
                    "timestamp": added.timestamp(),
                    "datetime": added.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                    "timestamp_desc": "%s added in known networks plist",
                    "extra_field_1": "Add reason: %s" % data[wifi]["AddReason"]
                }
                timeline.append(ts_event)
            except Exception as e:
                print(f"ERROR {filename} while extracting timestamp from {ssid}. Reason: {str(e)}. Record not inserted.")

                # WIFI modified
            try:
                updated = datetime.strptime(data[wifi]["UpdatedAt"], "%Y-%m-%d %H:%M:%S.%f")
                ts_event = {
                    "message": "WIFI %s added" % updated,
                    "timestamp": updated.timestamp(),
                    "datetime": updated.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                    "timestamp_desc": "%s updated in known networks plist",
                    "extra_field_1": "Add reason: %s" % data[wifi]["AddReason"]
                }
                timeline.append(ts_event)
            except Exception as e:
                print(f"ERROR {filename} while extracting timestamp from {ssid}. Reason: {str(e)}. Record not inserted.")

                # Password for wifi modified
            try:
                modified_password = datetime.strptime(data[wifi]["__OSSpecific__"]["WiFiNetworkPasswordModificationDate"], "%Y-%m-%d %H:%M:%S.%f")
                ts_event = {
                    "message": "Password for WIFI %s modified" % ssid,
                    "timestamp": modified_password.timestamp(),
                    "datetime": modified_password.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                    "timestamp_desc": "%s password modified in known networks plist",
                    "extra_field_1": "AP mode: %s" % data[wifi]["__OSSpecific__"]["AP_MODE"]
                }
                timeline.append(ts_event)
            except Exception as e:
                print(f"ERROR {filename} while extracting timestamp from {ssid}. Reason: {str(e)}. Record not inserted.")

    return True


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
    """
        Save timeline as JSONL (not JSON!!)
    """
    try:
        with open(ts_file, 'w') as f:
            for event in timeline:
                line = json.dumps(event)
                f.write("%s\n" % line)
    except Exception as e:
        print(f"ERROR: impossible to save timeline to {timeline}. Reason: {str(e)}")


def generate_timeline(jsondir, filename):
    """
    Generate the timeline and save it to filename
    """
    timeline = parse_json(jsondir)
    save_timeline(timeline, filename)
    return


# --------------------------------------------------------------------------- #


def main():
    """
        Main function
    """

    print(f"Running {version_string}\n")

    usage = "\n%prog -d JSON directory\n"

    parser = OptionParser(usage=usage)
    parser.add_option("-d", dest="inputdir",
                      action="store", type="string",
                      help="Directory containing JSON from parsers")
    parser.add_option("-o", dest="outputfile",
                      action="store", type="string",
                      help="JSON tile to save the timeline")
    (options, args) = parser.parse_args()

    # no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(-1)

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

# That's all folks ;)
