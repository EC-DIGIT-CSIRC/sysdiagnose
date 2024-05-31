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
import tempfile
import platform
import subprocess

version_string = "sysdiagnose-logarchive.py v2020-02-07 Version 1.0"

# ----- definition for parsing.py script -----#
# -----         DO NOT DELETE             ----#

parser_description = "Parsing system_logs.logarchive folder"


# --------------------------------------------#

# On 2023-04-13: using ndjson instead of json to avoid parsing issues.
# Based on manpage:
#       json      JSON output.  Event data is synthesized as an array of JSON dictionaries.
#
#       ndjson    Line-delimited JSON output.  Event data is synthesized as JSON dictionaries, each emitted on a single line.
#                 A trailing record, identified by the inclusion of a "finished" field, is emitted to indicate the end of events.
#
cmd_parsing_osx = "/usr/bin/log show %s --style ndjson"  # fastest and short version
# cmd_parsing_osx = "/usr/bin/log show %s --style json" # fastest and short version
# cmd_parsing_osx = "/usr/bin/log show %s --info --style json" # to enable debug, add --debug
# cmd_parsing_osx = "/usr/bin/log show %s --info --debug --style json"

# Linux parsing relies on UnifiedLogReader:
#       https://github.com/mandiant/macos-UnifiedLogs
# Follow instruction in the README.md in order to install it.
# TODO unifiedlog_parser is single threaded, either patch their code for multithreading support or do the magic here by parsing each file in a separate thread
cmd_parsing_linux = "unifiedlog_parser_json --input %s --output %s"
cmd_parsing_linux_test = ["unifiedlog_parser_json", "--help"]

# --------------------------------------------------------------------------- #


def get_log_files(log_root_path: str) -> list:
    log_folders = [
        'system_logs.logarchive/'
    ]
    return [os.path.join(log_root_path, log_folder) for log_folder in log_folders]


def get_logs(filename, ios_version=13, output=None):        # FIXME #18 hard coded default version?
    """
        Parse the system_logs.logarchive.  When running on OS X, use native tools.
        On other system use a 3rd party library.
    """
    if output is not None:
        output = os.path.join(output, "logarchive")
        os.makedirs(output, exist_ok=True)
    if (platform.system() == "Darwin"):
        if output is not None:
            output = os.path.join(output, "logarchive.json")
        data = get_logs_on_osx(filename, output)
        return data
    else:
        data = get_logs_on_linux(filename, output)
        return data
    return None


def parse_path(path: str) -> list | dict:
    return get_logs(path, output=None)


def parse_path_to_folder(path: str, output: str) -> bool:
    result = get_logs(path, output=output)
    if len(result['data']) > 0:
        return True
    else:
        print("Error:")
        print(json.dumps(result, indent=4))
        return False


def get_logs_on_osx(filename, output):
    cmd_line = cmd_parsing_osx % (filename)
    return __execute_cmd_and_get_result(cmd_line, output)


def get_logs_on_linux(filename, output):
    print("WARNING: using Mandiant UnifiedLogReader to parse logs, results will be less reliable than on OS X")
    # check if binary exists in PATH, if not, return an error
    try:
        subprocess.check_output(cmd_parsing_linux_test, universal_newlines=True)
    except FileNotFoundError:
        print("ERROR: UnifiedLogReader not found, please install it. See README.md for more information.")
        return ""

    if not output:
        with tempfile.TemporaryDirectory() as tmp_outpath:
            cmd_line = cmd_parsing_linux % (filename, tmp_outpath)
            # run the command and get the result
            __execute_cmd_and_get_result(cmd_line)
            # read the content of all the files to a variable, a bit crazy as it will eat memory massively
            # but at least it will be compatible with the overall logic, when needed
            data = []
            print("WARNING: combining all output files in memory, this is slow and eat a LOT of memory. Use with caution.")
            for fname in os.listdir(tmp_outpath):
                with open(os.path.join(tmp_outpath, fname), 'r') as f:
                    try:
                        json_data = json.load(f)
                        data.append(json_data)
                    except json.JSONDecodeError as e:
                        print(f"WARNING: error parsing JSON {fname}: {str(e)}")
            return data
            # tempfolder is cleaned automatically after the block
    else:
        cmd_line = cmd_parsing_linux % (filename, output)
        os.makedirs(output, exist_ok=True)
        # run the command and get the result, output file is mentioned in cmd_line
        data = __execute_cmd_and_get_result(cmd_line)
        return data


def __execute_cmd_and_get_result(command, outputfile=None):
    """
        Return None if it failed or the result otherwise.

        Outfile can have 3 values:
            - None: no output except return value
            - sys.stdout: print to stdout
            - path to a file to write to
    """
    cmd_array = command.split()
    result = {"data": []}

    with subprocess.Popen(cmd_array, stdout=subprocess.PIPE, universal_newlines=True) as process:
        if outputfile is None:
            for line in iter(process.stdout.readline, ''):
                try:
                    result['data'].append(json.loads(line))
                except Exception:
                    result['data'].append(line)
        elif outputfile == sys.stdout:
            for line in iter(process.stdout.readline, ''):
                print(line)
        else:
            with open(outputfile, "w") as outfd:
                for line in iter(process.stdout.readline, ''):
                    outfd.write(line)
                result['data'] = f'Output written to {outputfile}'

    return result
