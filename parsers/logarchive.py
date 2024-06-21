#! /usr/bin/env python3

# For Python3
# Script to parse system_logs.logarchive
# Author: david@autopsit.org
#
#
import os
import sys
import json
import tempfile
import platform
import subprocess
from datetime import datetime, timezone
from collections.abc import Generator


parser_description = 'Parsing system_logs.logarchive folder'


# --------------------------------------------#

# On 2023-04-13: using ndjson instead of json to avoid parsing issues.
# Based on manpage:
#       json      JSON output.  Event data is synthesized as an array of JSON dictionaries.
#
#       ndjson    Line-delimited JSON output.  Event data is synthesized as JSON dictionaries, each emitted on a single line.
#                 A trailing record, identified by the inclusion of a 'finished' field, is emitted to indicate the end of events.
#
cmd_parsing_osx = '/usr/bin/log show %s --style ndjson'  # fastest and short version
# cmd_parsing_osx = '/usr/bin/log show %s --style json' # fastest and short version
# cmd_parsing_osx = '/usr/bin/log show %s --info --style json' # to enable debug, add --debug
# cmd_parsing_osx = '/usr/bin/log show %s --info --debug --style json'

# Linux parsing relies on UnifiedLogReader:
#       https://github.com/mandiant/macos-UnifiedLogs
# Follow instruction in the README.md in order to install it.
# TODO unifiedlog_parser is single threaded, either patch their code for multithreading support or do the magic here by parsing each file in a separate thread
cmd_parsing_linux = 'unifiedlog_parser_json --input %s --output %s'
cmd_parsing_linux_test = ['unifiedlog_parser_json', '--help']
# --------------------------------------------------------------------------- #


def get_log_files(log_root_path: str) -> list:
    log_folders = [
        'system_logs.logarchive/'
    ]
    return [os.path.join(log_root_path, log_folder) for log_folder in log_folders]


def parse_path(path: str) -> list | dict:
    # OK, this is really inefficient as we're reading a file that we just wrote to a temporary folder
    # but who cares, nobody uses this function anyway...
    try:
        with tempfile.TemporaryDirectory() as tmp_outpath:
            parse_path_to_folder(path, tmp_outpath)
            with open(os.path.join(tmp_outpath, 'logarchive.json'), 'r') as f:
                return [json.loads(line) for line in f]
    except IndexError:
        return {'error': 'No system_logs.logarchive/ folder found in logs/ directory'}


def parse_path_to_folder(path: str, output_folder: str) -> bool:
    filename = get_log_files(path)[0]
    try:
        if (platform.system() == 'Darwin'):
            __convert_using_native_logparser(filename, output_folder)
        else:
            __convert_using_unifiedlogparser(filename, output_folder)
        return True
    except IndexError:
        print('Error: No system_logs.logarchive/ folder found in logs/ directory')
        return False


def __convert_using_native_logparser(filename: str, output_folder: str) -> list:
    with open(os.path.join(output_folder, 'logarchive.json'), 'w') as f_out:
        cmd_line = cmd_parsing_osx % (filename)
        # read each line, conver line by line and write the output directly to the new file
        for line in __execute_cmd_and_yield_result(cmd_line):
            try:
                entry_json = convert_entry_to_unifiedlog_format(json.loads(line))
                f_out.write(json.dumps(entry_json) + '\n')
            except json.JSONDecodeError as e:
                print(f"WARNING: error parsing JSON {line}: {str(e)}")


def __convert_using_unifiedlogparser(filename: str, output_folder: str) -> list:
    print('WARNING: using Mandiant UnifiedLogReader to parse logs, results will be less reliable than on OS X')
    # run the conversion tool, saving to a temp folder
    # read the created file/files, add timestamp
    # save to one single file in output folder

    # first check if binary exists in PATH, if not, return an error
    try:
        subprocess.check_output(cmd_parsing_linux_test, universal_newlines=True)
    except FileNotFoundError:
        print('ERROR: UnifiedLogReader not found, please install it. See README.md for more information.')
        return

    # really run the tool now
    with open(os.path.join(output_folder, 'logarchive.json'), 'w') as f_out:
        with tempfile.TemporaryDirectory() as tmp_outpath:
            cmd_line = cmd_parsing_linux % (filename, tmp_outpath)
            # run the command and get the result in our tmp_outpath folder
            __execute_cmd_and_get_result(cmd_line)
            # read each file, conver line by line and write the output directly to the new file
            for fname_reading in os.listdir(tmp_outpath):
                with open(os.path.join(tmp_outpath, fname_reading), 'r') as f:
                    for line in f:  # jsonl format - one json object per line
                        try:
                            entry_json = convert_entry_to_unifiedlog_format(json.loads(line))
                            f_out.write(json.dumps(entry_json) + '\n')
                        except json.JSONDecodeError as e:
                            print(f"WARNING: error parsing JSON {fname_reading}: {str(e)}")
            # tempfolder is cleaned automatically after the block


def __execute_cmd_and_yield_result(command: str) -> Generator[dict, None, None]:
    '''
        Return None if it failed or the result otherwise.

    '''
    cmd_array = command.split()
    with subprocess.Popen(cmd_array, stdout=subprocess.PIPE, universal_newlines=True) as process:
        for line in iter(process.stdout.readline, ''):
            yield line


def __execute_cmd_and_get_result(command, outputfile=None):
    '''
        Return None if it failed or the result otherwise.

        Outfile can have 3 values:
            - None: no output except return value
            - sys.stdout: print to stdout
            - path to a file to write to
    '''
    cmd_array = command.split()
    result = []

    with subprocess.Popen(cmd_array, stdout=subprocess.PIPE, universal_newlines=True) as process:
        if outputfile is None:
            for line in iter(process.stdout.readline, ''):
                try:
                    result.append(json.loads(line))
                except Exception:
                    result.append(line)
        elif outputfile == sys.stdout:
            for line in iter(process.stdout.readline, ''):
                print(line)
        else:
            with open(outputfile, 'w') as outfd:
                for line in iter(process.stdout.readline, ''):
                    outfd.write(line)
                result = f'Output written to {outputfile}'

    return result


def convert_entry_to_unifiedlog_format(entry: dict) -> dict:
    '''
        Convert the entry to unifiedlog format
    '''
    # already in the Mandiant unifiedlog format
    if 'event_type' in entry:
        entry['datetime'] = convert_unifiedlog_time_to_datetime(entry['time']).isoformat()
        return entry
    '''
    jq '. |= keys' logarchive-native.json > native_keys.txt
    sort native_keys.txt | uniq -c | sort -n > native_keys_sort_unique.txt
    '''

    mapper = {
        'creatorActivityID': 'activity_id',
        'messageType': 'log_type',
        # 'source': '',   # not present in the Mandiant format
        # 'backtrace': '',  # sub-dictionary
        'activityIdentifier': 'activity_id',
        'bootUUID': 'boot_uuid',   # remove - in the UUID
        'category': 'category',
        'eventMessage': 'message',
        'eventType': 'event_type',
        'formatString': 'raw_message',
        # 'machTimestamp': '',   # not present in the Mandiant format
        # 'parentActivityIdentifier': '',  # not present in the Mandiant format
        'processID': 'pid',
        'processImagePath': 'process',
        'processImageUUID': 'process_uuid',  # remove - in the UUID
        'senderImagePath': 'library',
        'senderImageUUID': 'library_uuid',   # remove - in the UUID
        # 'senderProgramCounter': '',  # not present in the Mandiant format
        'subsystem': 'subsystem',
        'threadID': 'thread_id',
        'timestamp': 'time',  # requires conversion
        'timezoneName': 'timezone_name',  # ignore timezone as time and timestamp are correct
        # 'traceID': '',  # not present in the Mandiant format
        'userID': 'euid'
    }

    new_entry = {}
    for key, value in entry.items():
        if key in mapper:
            new_key = mapper[key]
            if 'uuid' in new_key:  # remove - in UUID
                new_entry[new_key] = value.replace('-', '')
            else:
                new_entry[new_key] = value
        else:
            # keep the non-matching entries
            new_entry[key] = value
    # convert time
    new_entry['datetime'] = new_entry['time']
    new_entry['time'] = convert_native_time_to_unifiedlog_format(new_entry['time'])
    return new_entry


def convert_native_time_to_unifiedlog_format(time: str) -> int:
    timestamp = datetime.fromisoformat(time)
    return int(timestamp.timestamp() * 1000000000)


def convert_unifiedlog_time_to_datetime(time: int) -> datetime:
    # convert time to datetime object
    timestamp = datetime.fromtimestamp(time / 1000000000, tz=timezone.utc)
    return timestamp
