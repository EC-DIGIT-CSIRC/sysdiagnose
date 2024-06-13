#! /usr/bin/env python3

# For Python3
# Script to extract timestamp and generate a timesketch output
# Author: david@autopsit.org
#
# Important note: timestamp are in microseconds! standard epoch is in seconds. # FIXME is this correct?

import os
import json
from datetime import datetime, timezone
from parsers.logarchive import convert_entry_to_unifiedlog_format, convert_unifiedlog_time_to_datetime


analyser_description = "Generate a Timesketch compatible timeline"
analyser_format = "jsonl"


# Timesketch format:
# {"message": "A message","timestamp": 123456789,"datetime": "2015-07-24T19:01:01+00:00","timestamp_desc": "Write time","extra_field_1": "foo"}
timeline = []


def __extract_ts_mobileactivation(case_folder: str) -> bool:
    try:
        filename = 'mobileactivation.json'
        with open(os.path.join(case_folder, filename), 'r') as fd:
            data = json.load(fd)
            for event in data:
                ts_event = {
                    "message": "Mobile Activation",
                    "timestamp": event['timestamp'],
                    "datetime": event['datetime'],
                    "timestamp_desc": "Mobile Activation Time"
                }
                try:
                    ts_event["extra_field_1"] = "Build Version: %s" % event["build_version"]
                except KeyError:
                    # skip other type of event
                    # FIXME what should we do? the log file (now) contains nice timestamps, do we want to extract less, but summarized, data?
                    continue
                timeline.append(ts_event)
        return True
    except Exception as e:
        print(f"ERROR while extracting timestamp from {filename}. Reason: {str(e)}")
        return False


def __extract_ts_powerlogs(case_folder: str) -> bool:
    try:
        filename = 'powerlogs.json'
        with open(os.path.join(case_folder, filename), 'r') as fd:
            data = json.load(fd)

            # extract tables of interest
            __powerlogs__PLProcessMonitorAgent_EventPoint_ProcessExit(data)  # PLProcessMonitorAgent_EventPoint_ProcessExit
            __powerlogs__PLProcessMonitorAgent_EventBackward_ProcessExitHistogram(data)  # PLProcessMonitorAgent_EventBackward_ProcessExitHistogram
            __powerlogs__PLAccountingOperator_EventNone_Nodes(data)  # PLAccountingOperator_EventNone_Nodes
        return True
    except Exception as e:
        print(f"ERROR while extracting timestamp from {filename}. Reason: {str(e)}")
        return False


def __powerlogs__PLProcessMonitorAgent_EventPoint_ProcessExit(jdata):
    proc_exit = jdata["PLProcessMonitorAgent_EventPoint_ProcessExit"]
    for proc in proc_exit:
        timestamp = datetime.fromtimestamp(proc["timestamp"], tz=timezone.utc)

        extra_field = ""
        if "IsPermanent" in proc.keys():
            extra_field = "Is permanent: %d" % proc["IsPermanent"]
        ts_event = {
            "message": proc["ProcessName"],
            "timestamp": proc["timestamp"],
            "datetime": timestamp.isoformat(),
            "timestamp_desc": "Process Exit with reason code: %d reason namespace %d" % (proc["ReasonCode"], proc["ReasonNamespace"]),
            "extra_field_1": extra_field
        }
        timeline.append(ts_event)
    return


def __powerlogs__PLProcessMonitorAgent_EventBackward_ProcessExitHistogram(jdata):
    events = jdata["PLProcessMonitorAgent_EventBackward_ProcessExitHistogram"]
    for event in events:
        timestamp = datetime.fromtimestamp(event["timestamp"], tz=timezone.utc)
        ts_event = {
            "message": event["ProcessName"],
            "timestamp": event["timestamp"],
            "datetime": timestamp.isoformat(),
            "timestamp_desc": "Process Exit with reason code: %d reason namespace %d" % (event["ReasonCode"], event["ReasonNamespace"]),
            "extra_field_1": "Crash frequency: [0-5s]: %d, [5-10s]: %d, [10-60s]: %d, [60s+]: %d" % (event["0s-5s"], event["5s-10s"], event["10s-60s"], event["60s+"])
        }
        timeline.append(ts_event)
    return


def __powerlogs__PLAccountingOperator_EventNone_Nodes(jdata):
    eventnone = jdata["PLAccountingOperator_EventNone_Nodes"]
    for event in eventnone:
        timestamp = datetime.fromtimestamp(event["timestamp"], tz=timezone.utc)
        ts_event = {
            "message": event["Name"],
            "timestamp": event["timestamp"],
            "datetime": timestamp.isoformat(),
            "timestamp_desc": "PLAccountingOperator Event",
            "extra_field_1": "Is permanent: %d" % event["IsPermanent"]
        }
        timeline.append(ts_event)
    return


def __extract_ts_swcutil(case_folder: str) -> bool:
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
    filename = 'swcutil.json'
    try:
        with open(os.path.join(case_folder, filename), 'r') as fd:
            data = json.load(fd)
            if "db" in data.keys():
                for service in data["db"]:
                    try:
                        timestamp = datetime.strptime(service["Last Checked"], "%Y-%m-%d %H:%M:%S %z")
                        ts_event = {
                            "message": service["Service"],
                            "timestamp": float(timestamp.timestamp()),
                            "datetime": timestamp.isoformat(),
                            "timestamp_desc": "swcutil last checkeed",
                            "extra_field_1": "application: %s" % service["App ID"]
                        }
                        timeline.append(ts_event)
                    except KeyError:
                        # some entries do not have a Last Checked or timestamp field
                        # print(f"WARNING {filename} while extracting timestamp from {(service['Service'])} - {(service['App ID'])}. Record not inserted.")
                        pass
        return True
    except Exception as e:
        print(f"ERROR while extracting timestamp from {filename}. Reason {str(e)}")
        return False


def __extract_ts_accessibility_tcc(case_folder: str) -> bool:
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
    filename = 'accessibility_tcc.json'
    try:
        with open(os.path.join(case_folder, filename), 'r') as fd:
            data = json.load(fd)
            if "access" in data.keys():
                for access in data["access"]:
                    # create timeline entry
                    timestamp = datetime.fromtimestamp(access["last_modified"], tz=timezone.utc)
                    ts_event = {
                        "message": access["service"],
                        "timestamp": float(timestamp.timestamp()),
                        "datetime": timestamp.isoformat(),
                        "timestamp_desc": "Accessibility TC Last Modified",
                        "extra_field_1": "client: %s" % access["client"]
                    }
                    timeline.append(ts_event)
        return True
    except Exception as e:
        print(f"ERROR while extracting timestamp from {filename}. Reason {str(e)}")
        return False


def __extract_ts_shutdownlogs(case_folder: str) -> bool:
    filename = 'shutdownlogs.json'
    try:
        with open(os.path.join(case_folder, filename), 'r') as fd:
            data = json.load(fd)
            for ts, processes in data.items():
                try:
                    # create timeline entries
                    timestamp = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S+00:00")
                    for p in processes:
                        ts_event = {
                            "message": p["path"],
                            "timestamp": float(timestamp.timestamp()),
                            "datetime": timestamp.isoformat(),
                            "timestamp_desc": "Entry in shutdown.log",
                            "extra_field_1": "pid: %s" % p["pid"]
                        }
                        timeline.append(ts_event)
                except Exception as e:
                    print(f"WARNING: entry not parsed: {ts}. Reason: {str(e)}")
        return True
    except Exception as e:
        print(f"ERROR while extracting timestamp from {filename}. Reason: {str(e)}")
        return False


def __extract_ts_logarchive(case_folder: str) -> bool:
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
    logarchive_dir = os.path.join(case_folder, 'logarchive')
    no_error = True
    for file_in_logarchive_dir in os.listdir(logarchive_dir):
        try:
            with open(os.path.join(logarchive_dir, file_in_logarchive_dir), 'r') as fd:
                for line in fd:
                    # standardise the logarchive entryto unifiedlog format
                    try:
                        trace = convert_entry_to_unifiedlog_format(json.loads(line))
                        # create timeline entry
                        timestamp = convert_unifiedlog_time_to_datetime(trace["time"])
                        ts_event = {
                            "message": trace["message"],
                            "timestamp": timestamp.timestamp(),
                            "datetime": timestamp.isoformat(),
                            "timestamp_desc": "Entry in logarchive: %s" % trace["event_type"],
                            "extra_field_1": f"subsystem: {trace["subsystem"]}; process_uuid: {trace["process_uuid"]}; process: {trace["process"]}; library: {trace["library"]}; library_uuid: {trace["library_uuid"]}"
                        }
                        timeline.append(ts_event)
                    except KeyError as e:
                        print(f"WARNING: trace not parsed: {trace}. Error {e}")
        except Exception as e:
            print(f"ERROR while extracting timestamp from {file_in_logarchive_dir}. Reason: {str(e)}")
            no_error = False
    return no_error


def __extract_ts_wifisecurity(case_folder: str) -> bool:
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
    filename = 'wifisecurity.json'
    try:
        with open(os.path.join(case_folder, filename), 'r') as fd:
            data = json.load(fd)
            for wifi in data:
                # create timeline entry
                ctimestamp = datetime.strptime(wifi["cdat"], "%Y-%m-%d %H:%M:%S %z")
                mtimestamp = datetime.strptime(wifi["mdat"], "%Y-%m-%d %H:%M:%S %z")

                # Event 1: creation
                ts_event = {
                    "message": wifi["acct"],
                    "timestamp": float(ctimestamp.timestamp()),
                    "datetime": ctimestamp.isoformat(),
                    "timestamp_desc": "SSID added to known secured WIFI list",
                    "extra_field_1": wifi["accc"]
                }
                timeline.append(ts_event)

                # Event 2: modification
                ts_event = {
                    "message": wifi["acct"],
                    "timestamp": float(mtimestamp.timestamp()),
                    "datetime": mtimestamp.isoformat(),
                    "timestamp_desc": "SSID modified into the secured WIFI list",
                    "extra_field_1": wifi["accc"]
                }
                timeline.append(ts_event)
        return True
    except Exception as e:
        print(f"ERROR while extracting timestamp from {filename}. Reason {str(e)}")
        return False


def __extract_ts_wifi_known_networks(case_folder: str) -> bool:
    filename = 'wifi_known_networks.json'
    try:
        with open(os.path.join(case_folder, filename), 'r') as fd:
            data = json.load(fd)
            for item in data.values():
                ssid = item["SSID"]
                # WIFI added
                try:
                    added = datetime.strptime(item["AddedAt"], "%Y-%m-%d %H:%M:%S.%f")
                    ts_event = {
                        "message": "WIFI %s added" % ssid,
                        "timestamp": added.timestamp(),
                        "datetime": added.isoformat(),
                        "timestamp_desc": "%s added in known networks plist",
                        "extra_field_1": "Add reason: %s" % item["AddReason"]
                    }
                    timeline.append(ts_event)
                except KeyError:
                    # some wifi networks do not have an AddedAt field
                    # print(f"ERROR {filename} while extracting timestamp from {ssid}. Reason: {str(e)}. Record not inserted.")
                    pass

                # WIFI modified
                try:
                    updated = datetime.strptime(item["UpdatedAt"], "%Y-%m-%d %H:%M:%S.%f")
                    ts_event = {
                        "message": "WIFI %s added" % updated,
                        "timestamp": updated.timestamp(),
                        "datetime": updated.isoformat(),
                        "timestamp_desc": "%s updated in known networks plist",
                        "extra_field_1": "Add reason: %s" % item["AddReason"]
                    }
                    timeline.append(ts_event)
                except KeyError:
                    # some wifi networks do not have an UpdatedAt field
                    # print(f"ERROR {filename} while extracting timestamp from {ssid}. Reason: {str(e)}. Record not inserted.")
                    pass

                # Password for wifi modified
                try:
                    modified_password = datetime.strptime(item["__OSSpecific__"]["WiFiNetworkPasswordModificationDate"], "%Y-%m-%d %H:%M:%S.%f")
                    ts_event = {
                        "message": "Password for WIFI %s modified" % ssid,
                        "timestamp": modified_password.timestamp(),
                        "datetime": modified_password.isoformat(),
                        "timestamp_desc": "%s password modified in known networks plist",
                        "extra_field_1": "AP mode: %s" % item["__OSSpecific__"]["AP_MODE"]
                    }
                    timeline.append(ts_event)
                except KeyError:
                    # some wifi networks do not have a password modification date
                    # print(f"ERROR {filename} while extracting timestamp from {ssid}. Reason: {str(e)}. Record not inserted.")
                    pass
        return True
    except Exception as e:
        print(f"ERROR while extracting timestamp from {filename}. Reason {str(e)}")
        return False


def analyse_path(case_folder: str, output_file: str = 'timeliner.jsonl') -> bool:
    # Get all the functions that start with '__extract_ts_'
    # and call these with the case_folder as parameter
    # FIXME move the for loop within the file write and change to yield
    for func in globals():
        if func.startswith('__extract_ts_'):
            globals()[func](case_folder)  # call the function

    try:
        with open(output_file, 'w') as f:
            for event in timeline:
                line = json.dumps(event)
                f.write(line)
                f.write("\n")
    except Exception as e:
        print(f"ERROR: impossible to save timeline to {output_file}. Reason: {str(e)}")
        return False
    return True
